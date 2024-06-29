# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject, Gst, GstAudio, Gtk

from blanket.preset import Preset
from blanket.settings import Settings


class MainPlayer(GObject.GObject, Gio.ListModel):
    """
    Virtual app sounds player

    It also implements Gio.ListModel and stores the app sound list.
    """

    _instance = None
    _cookie = 0
    _sounds = []  # Sound list
    _initial_seek = False

    __gtype_name__ = 'MainPlayer'
    __gsignals__ = {
        'preset-changed': (GObject.SIGNAL_RUN_FIRST, None, (GObject.Object,)),
        'reset-volumes': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    playing: bool = GObject.Property(type=bool, default=True)  # type: ignore
    volume: float = GObject.Property(type=float, default=0)  # type: ignore

    @classmethod
    def get(cls):
        """Return an active instance of MainPlayer."""
        if cls._instance is None:
            cls._instance = MainPlayer()
        return cls._instance

    def __init__(self):
        super().__init__()

        self.connect('notify::playing', self._on_playing)
        Settings.get().connect('preset-changed', self._on_preset_changed)

        self.__add_item = GObject.GObject()  # Fake sound that adds new sounds
        self.__add_item.playing = False  # type: ignore

        # GStreamer pipeline
        self.pipe = Gst.Pipeline.new('blanket')

        # Mixer element
        self.mixer = Gst.ElementFactory.make('adder', 'mixer')
        # Convert element
        convert = Gst.ElementFactory.make('audioconvert', 'convert')
        # Sink element
        sink = Gst.ElementFactory.make('playsink', 'playsink')

        if self.mixer and convert and sink:
            self.pipe.add(self.mixer)
            self.pipe.add(convert)
            self.pipe.add(sink)

            # Link elements
            self.mixer.link(convert)
            convert.link(sink)

            # Make main player control sink volume
            sink.bind_property(
                'volume',
                self,
                'volume',
                GObject.BindingFlags.BIDIRECTIONAL,
                self._vol_to_sink,
                self._vol_to_ui,
            )

            # Start the playback
            self.pipe.set_state(Gst.State.PLAYING)
            self.pipe.set_state(Gst.State.PAUSED)  # Start paused

    def _vol_to_sink(self, _bind, from_val: float):
        return GstAudio.StreamVolume.convert_volume(
            GstAudio.StreamVolumeFormat.LINEAR,
            GstAudio.StreamVolumeFormat.CUBIC,
            from_val,
        )

    def _vol_to_ui(self, _bind, from_val: float):
        return GstAudio.StreamVolume.convert_volume(
            GstAudio.StreamVolumeFormat.CUBIC,
            GstAudio.StreamVolumeFormat.LINEAR,
            from_val,
        )

    def mute_vol_zero(self):
        for sound in self:
            if sound.saved_volume == 0:
                sound.playing = False

    def reset_volumes(self):
        self.emit('reset-volumes')

    def next_preset(self):
        if not self.can_next:
            return

        presets = Settings.get().presets
        index = presets.index(Settings.get().active_preset)
        Settings.get().active_preset = presets[index + 1]

    def prev_preset(self):
        if not self.can_prev:
            return

        presets = Settings.get().presets
        index = presets.index(Settings.get().active_preset)
        Settings.get().active_preset = presets[index - 1]

    @property
    def can_next(self) -> bool:
        presets = Settings.get().presets
        index = presets.index(Settings.get().active_preset)

        return index != len(presets) - 1 and len(presets) > 1

    @property
    def can_prev(self) -> bool:
        presets = Settings.get().presets
        index = presets.index(Settings.get().active_preset)

        return index > 0 and len(presets) > 1

    def _on_playing(self, _player, _param):
        # Toggle suspension inhibition when playing
        app = Gtk.Application.get_default()
        if app:
            if self.playing:
                self._cookie = app.inhibit(  # type: ignore
                    None, Gtk.ApplicationInhibitFlags.SUSPEND, 'Playback in progress'
                )
            elif self._cookie != 0:
                app.uninhibit(self._cookie)  # type: ignore

        # Seek once for segment events to be sent
        if not self._initial_seek:
            self.pipe.seek_simple(
                Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT, 0
            )
            self._initial_seek = True

        # Toggle pipeline playing state
        if self.playing:
            self.pipe.set_state(Gst.State.PLAYING)
        else:
            self.pipe.set_state(Gst.State.PAUSED)

    def _on_preset_changed(self, _settings, preset_id):
        self.emit('preset-changed', Preset(preset_id))

    """
    ListModel methods

    This model keeps a fake last item that serves for the add sound item
    """

    def __iter__(self):
        return iter(self._sounds)

    def do_get_item(self, position: int) -> GObject.Object:
        if position == len(self._sounds):
            return self.__add_item  # Return plain GObject of Add sound item
        return self._sounds[position]

    def do_get_item_type(self):
        return GObject.Object

    def do_get_n_items(self) -> int:
        return len(self._sounds) + 1  # Add fake sound to total of items

    def append(self, sound: GObject.Object):
        self._sounds.append(sound)
        self.items_changed(len(self._sounds) - 1, 0, 1)

    def remove(self, position: int):
        del self._sounds[position]
        self.items_changed(position, 1, 0)

    def get_by_name(self, name: str) -> tuple[GObject.Object, int] | tuple[None, None]:
        for position, sound in enumerate(self._sounds):
            if sound.name == name:
                return (sound, position)

        return (None, None)
