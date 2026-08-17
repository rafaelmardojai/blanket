# Copyright 2020 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING, Callable

from gi.repository import GLib, Gst

if TYPE_CHECKING:
    from blanket.sound import Sound

# A sound whose duration is not known yet cannot be looped, so wait for it
LOOP_RETRY_INTERVAL = 200
LOOP_RETRIES = 25


class Player(Gst.Bin):
    """
    Playback of a single sound, as a branch of the shared pipeline

    The branch is only attached to the mixer while the sound is audible, so
    silent sounds cost neither a decoder nor its threads.
    """

    def __init__(self, sound: "Sound", **kwargs):
        super().__init__(**kwargs)

        self._sound = sound
        self._looping = False

        decoder = Gst.ElementFactory.make("uridecodebin", None)
        convert = Gst.ElementFactory.make("audioconvert", None)
        # audiomixer does not convert between formats, so a sound recorded at
        # another rate has to be resampled before it reaches the mixer
        resample = Gst.ElementFactory.make("audioresample", None)
        caps = Gst.ElementFactory.make("capsfilter", None)
        volume = Gst.ElementFactory.make("volume", None)

        if not decoder or not convert or not resample or not caps or not volume:
            print("Error: could not create the GStreamer elements for a sound")
            return

        decoder.props.uri = sound.uri  # type: ignore

        # Every branch has to reach the mixer in the same format, and mixing at
        # the rate the sounds already are in keeps the resamplers idle.
        caps.props.caps = Gst.Caps.from_string(  # type: ignore
            "audio/x-raw,format=F32LE,rate=44100,channels=2,layout=interleaved"
        )

        for element in (decoder, convert, resample, caps, volume):
            self.add(element)

        convert.link(resample)
        resample.link(caps)
        caps.link(volume)

        self._convert = convert
        self._volume = volume

        if vol_pad := volume.get_static_pad("src"):
            self.add_pad(Gst.GhostPad.new("src", vol_pad))
        decoder.connect("pad-added", self._on_pad_added)

    @property
    def volume(self) -> float:
        return self._volume.props.volume  # type: ignore

    @volume.setter
    def volume(self, value: float):
        self._volume.props.volume = value  # type: ignore

    """
    Loop handling

    The sound has no sink of its own, so the pipeline never posts SEGMENT_DONE
    for it. The matching event is caught as it leaves the branch instead.
    """

    def _on_pad_added(self, _decoder: Gst.Element, pad: Gst.Pad):
        sink_pad = self._convert.get_static_pad("sink")
        if sink_pad and not sink_pad.is_linked():
            pad.link(sink_pad)

        src_pad = self.get_static_pad("src")
        if src_pad is None:
            return

        # Seeking before the caps are negotiated fails, so wait for data
        src_pad.add_probe(Gst.PadProbeType.BUFFER, self._on_first_buffer)
        src_pad.add_probe(Gst.PadProbeType.EVENT_DOWNSTREAM, self._on_branch_event)

    def _on_first_buffer(self, _pad: Gst.Pad, _info: Gst.PadProbeInfo):
        GLib.idle_add(self._start_loop, 0)
        return Gst.PadProbeReturn.REMOVE

    def _start_loop(self, attempt: int):
        if self._looping:
            return GLib.SOURCE_REMOVE

        if self._seek(flush=True):
            self._looping = True
        else:
            self._retry_loop(self._start_loop, attempt)

        return GLib.SOURCE_REMOVE

    def _restart_loop(self, attempt: int):
        if not self._seek(flush=False):
            self._retry_loop(self._restart_loop, attempt)

        return GLib.SOURCE_REMOVE

    def _retry_loop(self, callback: Callable[[int], bool], attempt: int):
        """
        Try again later when the duration is not known yet

        Retrying from the idle callback itself would only spin the main loop,
        and a sound whose duration never resolves would spin it forever.
        """
        if attempt >= LOOP_RETRIES:
            print(f"Error: could not loop {self._sound.name}, its duration is unknown")
            return

        GLib.timeout_add(LOOP_RETRY_INTERVAL, callback, attempt + 1)

    def _on_branch_event(self, _pad, info: Gst.PadProbeInfo):
        event = info.get_event()

        if event and event.type is Gst.EventType.SEGMENT_DONE:
            GLib.idle_add(self._restart_loop, 0)
            return Gst.PadProbeReturn.DROP

        if event and event.type is Gst.EventType.EOS:
            # Letting it through would end the whole pipeline
            return Gst.PadProbeReturn.DROP

        return Gst.PadProbeReturn.OK

    def _seek(self, flush: bool) -> bool:
        # The segment has to be given an explicit end: seeking before the
        # duration is known would leave an empty one, looping on itself.
        known, duration = self.query_duration(Gst.Format.TIME)
        if not known or duration <= 0:
            return False

        flags = Gst.SeekFlags.SEGMENT
        if flush:
            flags |= Gst.SeekFlags.FLUSH

        return self.seek(
            1.0,
            Gst.Format.TIME,
            flags,
            Gst.SeekType.SET,
            0,
            Gst.SeekType.SET,
            duration,
        )
