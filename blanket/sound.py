# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GObject, Gst

from blanket.define import RES_PATH
from blanket.main_player import MainPlayer
from blanket.settings import Settings


class Sound(GObject.Object):
    """
    Describe a sound with it's properties
    """

    __gtype_name__ = 'Sound'

    playing: bool = GObject.Property(type=bool, default=False)  # type: ignore
    title: str = GObject.Property(type=str)  # type: ignore
    icon_name: str = GObject.Property(type=str)  # type: ignore

    def __init__(
        self,
        name: str,
        uri: str | None = None,
        title: str | None = None,
        custom: bool | None = False,
        noise=False,
        **kwargs,
    ):
        super().__init__()

        resource = f'resource:{RES_PATH}/sounds/{name}.ogg'
        icon = 'com.rafaelmardojai.Blanket-{}'

        # Sound properties
        self.name = name
        self.uri = uri if uri else resource
        self.title = title if title else name
        self.icon_name = icon.format('sound-wave' if custom else name)
        self.custom = custom
        self.noise = noise

        self._sink_pad = None  # Main player sink pad for this sound
        self._sounbin = None  # Gstreamer bin for this sound

        self.setup_audio()

        # Playing state
        self.connect('notify::playing', self._playing_changed)
        if not self.saved_mute:
            self.playing = True

        # Connect mainplayer preset-changed signal
        MainPlayer.get().connect('preset-changed', self._on_preset_changed)
        # Connect mainplayer reset-volumes signal
        MainPlayer.get().connect('reset-volumes', self._on_reset_volumes)

    def setup_audio(self):
        def pad_added(element, pad):
            pad.link(self._sink_pad)

        # Get audio mixer sink pad for the sound
        self._sink_pad = MainPlayer.get().mixer.get_request_pad('sink_%u')  # type: ignore

        if self._sink_pad:
            # Start with pad muted
            # self._sink_pad.props.mute = True  # type: ignore

            # Setup sound
            if not self.noise:
                self._sounbin = _SoundBin(self.uri)
                self._sounbin.connect('pad-added', pad_added)
            else:
                self._sounbin = _NoiseBin(self.name)

            # Add to main pipeline
            MainPlayer.get().pipe.add(self._sounbin)

            # Link noise src to sink
            if self.noise:
                bin_src_pad = self._sounbin.get_static_pad('src')
                if bin_src_pad:
                    bin_src_pad.link(self._sink_pad)

            # Bin playing state
            self._sounbin.set_state(Gst.State.PLAYING)

    @GObject.Property(type=float)
    def saved_volume(self) -> float:  # type: ignore
        return Settings.get().get_sound_volume(self.name)

    @saved_volume.setter
    def saved_volume(self, volume: float):
        if self._sounbin is None:
            return

        volume = round(volume, 2)
        self._sounbin.volume = volume
        Settings.get().set_sound_volume(self.name, volume)

        if volume != 0 and not self.playing:
            self.playing = True

    @property
    def saved_mute(self) -> bool:
        return Settings.get().get_sound_mute(self.name)

    @saved_mute.setter
    def saved_mute(self, mute: bool):
        Settings.get().set_sound_mute(self.name, mute)

    def remove(self):
        """Remove sound if it is custom"""
        if self.custom:
            # Remove from settings
            Settings.get().remove_custom_audio(self.name)

            # TODO: Properly remove GStreamer
            # Remove from GStreamer
            self._sounbin.set_state(Gst.State.NULL)  # type: ignore
            MainPlayer.get().mixer.release_request_pad(self._sink_pad)  # type: ignore

    def _playing_changed(self, _object, _pspec):
        if self._sounbin is None:
            return

        # Toggle player mute state
        if self.playing:
            self._sounbin.mute = False
            if self.saved_volume > 0:
                self._sounbin.volume = self.saved_volume
            else:
                self.saved_volume = 0.5
        else:
            self._sounbin.mute = True

        self.saved_mute = not self.playing  # Save playing state

    def _on_preset_changed(self, _player, _preset):
        self.notify('saved_volume')
        self.playing = not self.saved_mute

    def _on_reset_volumes(self, _player):
        self.saved_volume = 0.0
        self.playing = False


class _BaseBin(Gst.Bin):
    """
    Base bin with shared logic for noises and sounds

    Converts raw audio, resamples and manages volume
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Convert element
        self._convert = Gst.ElementFactory.make('audioconvert', None)
        # Resample element
        self._resample = Gst.ElementFactory.make('audioresample', None)
        # Volume element
        self._volume = Gst.ElementFactory.make('volume', None)

        if self._convert is None or self._resample is None or self._volume is None:
            raise Exception('Could not find GStreamer elements to create _BaseBin!')

        self.add(self._convert)
        self.add(self._resample)
        self.add(self._volume)

        # Start muted
        self._volume.props.mute = True  # type: ignore

        # Link convert with volume
        self._convert.link(self._resample)
        self._resample.link(self._volume)

    @property
    def volume(self) -> float:
        return self._volume.props.volume or 0  # type: ignore

    @volume.setter
    def volume(self, vol: float):
        self._volume.props.volume = vol  # type: ignore

    @property
    def mute(self) -> bool:
        return self._volume.props.mute or False  # type: ignore

    @mute.setter
    def mute(self, mute: bool):
        self._volume.props.mute = mute  # type: ignore


class _SoundBin(_BaseBin):
    """
    Private Gst.Bin to play Blanket's sounds

    Reads and decodes the resource sound files using uridecodebin.

    It also is responsible of implementing looping.
    """

    def __init__(self, uri: str, **kwargs):
        super().__init__(**kwargs)

        # SRC pad template
        self._pad_template = Gst.PadTemplate.new(
            'src_%u',
            Gst.PadDirection.SRC,
            Gst.PadPresence.SOMETIMES,
            Gst.Caps.new_any(),
        )

        if self._pad_template:
            self.add_pad_template(self._pad_template)

        # Decode element
        self._uridecodebin = Gst.ElementFactory.make('uridecodebin', None)

        if self._uridecodebin is None:
            raise Exception('Could not find GStreamer elements to create _SoundBin!')

        self.add(self._uridecodebin)

        self._uridecodebin.props.uri = uri  # type: ignore
        self._uridecodebin.connect('pad-added', self._on_pad_added)

    def _on_pad_added(self, _element: Gst.Element, pad: Gst.Pad):
        # Link decode and convert
        convert_sink_pad = self._convert.get_static_pad('sink')  # type: ignore
        if convert_sink_pad:
            pad.link(convert_sink_pad)

        # Proxy volume to our bin src pad
        volume_src_pad = self._volume.get_static_pad('src')  # type: ignore
        if self._pad_template and volume_src_pad:
            proxy_pad = Gst.GhostPad.new_from_template(
                'src_%u', volume_src_pad, self._pad_template
            )
            if proxy_pad:
                self.add_pad(proxy_pad)

        # Add prove to check events and loop if needed
        pad.add_probe(Gst.PadProbeType.EVENT_DOWNSTREAM, self._on_probe)

    def _on_probe(self, pad: Gst.Pad, info: Gst.PadProbeInfo) -> Gst.PadProbeReturn:
        info_event = info.get_event()

        if info_event:
            # If segment done, send a seek event to go back to the beginning
            if info_event.type is Gst.EventType.SEGMENT_DONE and self._uridecodebin:
                success, duration = self._uridecodebin.query_duration(Gst.Format.TIME)
                if success:
                    event = Gst.Event.new_seek(
                        1.0,
                        Gst.Format.TIME,
                        Gst.SeekFlags.SEGMENT,
                        Gst.SeekType.SET,
                        0,
                        Gst.SeekType.SET,
                        duration,
                    )
                    if event:
                        pad.send_event(event)

        return Gst.PadProbeReturn.PASS


class _NoiseBin(_BaseBin):
    """
    Private Gst.Bin to play Blanket's noises

    Internally just maps to a audiotestsrc.
    """

    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)

        # SRC pad template
        pad_template = Gst.PadTemplate.new(
            'src',
            Gst.PadDirection.SRC,
            Gst.PadPresence.ALWAYS,
            Gst.Caps.new_any(),
        )

        if pad_template:
            self.add_pad_template(pad_template)

        noise = Gst.ElementFactory.make('audiotestsrc', None)

        if noise is None:
            raise Exception('Could not find GStreamer elements to create _NoiseBin!')

        self.add(noise)

        # Set noise properties
        noise.props.freq = 100  # type: ignore
        noise.props.wave = name  # type: ignore
        noise.props.is_live = True  # type: ignore

        noise.link(self._convert)  # type: ignore

        # Proxy convert to our bin src pad
        volume_src_pad = self._volume.get_static_pad('src')  # type: ignore
        if pad_template and volume_src_pad:
            proxy_pad = Gst.GhostPad.new_from_template(
                'src', volume_src_pad, pad_template
            )
            if proxy_pad:
                self.add_pad(proxy_pad)
