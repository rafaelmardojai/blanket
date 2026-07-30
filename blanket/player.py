# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GLib, Gst

from blanket.main_player import MainPlayer


class Player:
    """
    Playback of a single sound, as a branch of the shared pipeline

    The branch is only attached to the mixer while the sound is audible, so
    silent sounds cost neither a decoder nor its threads.
    """

    def __init__(self, sound):
        self.sound = sound
        # Create a var to save saved volume
        self.saved_volume = 0.0

        self._bin = None
        self._convert = None
        self._volume = None
        self._mixer_pad = None
        self._looping = False

        # Connect mainplayer volume signal
        self.volume_hdlr = MainPlayer.get().connect(
            "notify::volume", self._on_main_volume_changed
        )

    def set_virtual_volume(self, volume: float):
        # Get last saved sound volume
        self.saved_volume = volume

        if self.saved_volume > 0:
            self._attach()
            # Multiply sound volume with mainplayer volume
            self._volume.props.volume = self.saved_volume * MainPlayer.get().volume  # type: ignore
        else:
            # A silent sound keeps no pipeline around
            self._detach()

    def remove(self):
        # Drop the branch from the pipeline
        self._detach()
        # Disconnect main player signals
        MainPlayer.get().disconnect(self.volume_hdlr)

    def _on_main_volume_changed(self, _player, _volume):
        # Set volume again when mainplayer volume changes
        self.set_virtual_volume(self.saved_volume)

    """
    Branch handling
    """

    def _attach(self):
        if self._bin is not None:
            return

        player = MainPlayer.get()

        self._bin = Gst.Bin.new(f"sound-{self.sound.name}")
        decoder = Gst.ElementFactory.make("uridecodebin", None)
        convert = Gst.ElementFactory.make("audioconvert", None)
        # audiomixer does not convert between formats, so a sound recorded at
        # another rate has to be resampled before it reaches the mixer
        resample = Gst.ElementFactory.make("audioresample", None)
        caps = Gst.ElementFactory.make("capsfilter", None)
        volume = Gst.ElementFactory.make("volume", None)

        if not all((decoder, convert, resample, caps, volume)):
            raise RuntimeError("Could not create the GStreamer sound elements")

        decoder.props.uri = self.sound.uri  # type: ignore
        # Every branch has to reach the mixer in the same format, and mixing at
        # the rate the sounds already are in keeps the resamplers idle
        caps.props.caps = Gst.Caps.from_string(  # type: ignore
            "audio/x-raw,format=F32LE,rate=44100,channels=2,layout=interleaved"
        )

        for element in (decoder, convert, resample, caps, volume):
            self._bin.add(element)

        convert.link(resample)  # type: ignore
        resample.link(caps)  # type: ignore
        caps.link(volume)  # type: ignore

        self._convert = convert
        self._volume = volume
        self._bin.add_pad(
            Gst.GhostPad.new("src", volume.get_static_pad("src"))  # type: ignore
        )
        decoder.connect("pad-added", self._on_pad_added)  # type: ignore

        player.pipeline.add(self._bin)
        self._mixer_pad = player.mixer.request_pad_simple("sink_%u")  # type: ignore

        src_pad = self._bin.get_static_pad("src")
        # Shift the branch to where the mixer already is, or it would produce
        # buffers the mixer considers long past and drops
        src_pad.set_offset(player.branch_offset())  # type: ignore
        src_pad.link(self._mixer_pad)  # type: ignore

        player.branch_added()
        self._bin.sync_state_with_parent()

    def _detach(self):
        if self._bin is None:
            return

        sound_bin, mixer_pad = self._bin, self._mixer_pad
        self._bin = None
        self._convert = None
        self._volume = None
        self._mixer_pad = None
        self._looping = False

        state = MainPlayer.get().pipeline.get_state(0).state
        if state is not Gst.State.PLAYING:
            # Nothing is streaming, so a blocking probe would never be called
            self._destroy_branch(sound_bin, mixer_pad)
            return

        # Block the branch before tearing it down, so the mixer never sees a
        # half-removed pad
        pad = sound_bin.get_static_pad("src")
        pad.add_probe(  # type: ignore
            Gst.PadProbeType.IDLE,
            lambda _pad, _info: self._on_branch_blocked(sound_bin, mixer_pad),
        )

    def _on_branch_blocked(self, sound_bin: Gst.Bin, mixer_pad):
        # States cannot be changed from a streaming thread
        GLib.idle_add(self._destroy_branch, sound_bin, mixer_pad)
        return Gst.PadProbeReturn.REMOVE

    def _destroy_branch(self, sound_bin: Gst.Bin, mixer_pad):
        player = MainPlayer.get()

        sound_bin.get_static_pad("src").unlink(mixer_pad)  # type: ignore
        player.mixer.release_request_pad(mixer_pad)  # type: ignore
        sound_bin.set_state(Gst.State.NULL)
        player.pipeline.remove(sound_bin)
        player.branch_removed()

        return GLib.SOURCE_REMOVE

    """
    Loop handling

    The sound has no sink of its own, so the pipeline never posts SEGMENT_DONE
    for it. The matching event is caught as it leaves the branch instead.
    """

    def _on_pad_added(self, _decoder, pad: Gst.Pad):
        if self._bin is None or self._convert is None:
            return

        sink_pad = self._convert.get_static_pad("sink")
        if sink_pad and not sink_pad.is_linked():
            pad.link(sink_pad)

        src_pad = self._bin.get_static_pad("src")
        if src_pad is None:
            return

        # Seeking before the caps are negotiated fails, so wait for data
        src_pad.add_probe(Gst.PadProbeType.BUFFER, self._on_first_buffer)
        src_pad.add_probe(Gst.PadProbeType.EVENT_DOWNSTREAM, self._on_branch_event)

    def _on_first_buffer(self, _pad, _info):
        GLib.idle_add(self._start_loop)
        return Gst.PadProbeReturn.REMOVE

    def _start_loop(self):
        if self._bin is None or self._looping:
            return GLib.SOURCE_REMOVE

        if not self._seek(flush=True):
            return GLib.SOURCE_CONTINUE

        self._looping = True
        return GLib.SOURCE_REMOVE

    def _restart_loop(self):
        if self._bin is None:
            return GLib.SOURCE_REMOVE

        if not self._seek(flush=False):
            return GLib.SOURCE_CONTINUE

        return GLib.SOURCE_REMOVE

    def _on_branch_event(self, _pad, info: Gst.PadProbeInfo):
        event = info.get_event()

        if event and event.type is Gst.EventType.SEGMENT_DONE:
            GLib.idle_add(self._restart_loop)
            return Gst.PadProbeReturn.DROP

        if event and event.type is Gst.EventType.EOS:
            # Letting it through would end the whole pipeline
            return Gst.PadProbeReturn.DROP

        return Gst.PadProbeReturn.OK

    def _seek(self, flush: bool) -> bool:
        if self._bin is None:
            return False

        # The segment has to be given an explicit end: seeking before the
        # duration is known would leave an empty one, looping on itself
        known, duration = self._bin.query_duration(Gst.Format.TIME)
        if not known or duration <= 0:
            return False

        flags = Gst.SeekFlags.SEGMENT
        if flush:
            flags |= Gst.SeekFlags.FLUSH

        return self._bin.seek(
            1.0,
            Gst.Format.TIME,
            flags,
            Gst.SeekType.SET,
            0,
            Gst.SeekType.SET,
            duration,
        )
