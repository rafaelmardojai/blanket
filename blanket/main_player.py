# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject, Gst, Gtk

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

    __gtype_name__ = "MainPlayer"
    __gsignals__ = {
        "preset-changed": (GObject.SIGNAL_RUN_FIRST, None, (GObject.Object,)),
        "reset-volumes": (GObject.SIGNAL_RUN_FIRST, None, ()),
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
        self.connect("notify::playing", self._on_playing)
        Settings.get().connect("preset-changed", self._on_preset_changed)
        Settings.get().connect(
            "changed::inhibit-suspension", self._on_settings_inhibition
        )

        self.__add_item = GObject.GObject()  # Fake sound that adds new sounds
        self.__add_item.playing = False  # type: ignore

        self._setup_pipeline()

    def _setup_pipeline(self):
        """
        Set up the single pipeline shared by every sound

        Each playing sound is a branch feeding the mixer, so all of them are
        decoded into one stream and go out through a single audio sink.
        """
        self._branches = 0

        self.pipeline = Gst.Pipeline.new("blanket")
        self.mixer = Gst.ElementFactory.make("audiomixer", "mixer")
        convert = Gst.ElementFactory.make("audioconvert", None)
        resample = Gst.ElementFactory.make("audioresample", None)
        sink = Gst.ElementFactory.make("autoaudiosink", None)

        if not all((self.mixer, convert, resample, sink)):
            raise RuntimeError("Could not create the GStreamer playback elements")

        for element in (self.mixer, convert, resample, sink):
            self.pipeline.add(element)

        self.mixer.link(convert)  # type: ignore
        convert.link(resample)  # type: ignore
        resample.link(sink)  # type: ignore

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_pipeline_error)

    def branch_added(self):
        self._branches += 1
        self._sync_pipeline_state()

    def branch_removed(self):
        self._branches -= 1
        self._sync_pipeline_state()

    def branch_offset(self) -> int:
        """
        Running time a branch about to be attached has to be shifted by

        The mixer works in running time, so a branch joining a pipeline that
        already advanced would be mixed in the past and dropped.
        """
        state = self.pipeline.get_state(0).state

        if state is Gst.State.PLAYING:
            offset = self.mixer.get_current_running_time()  # type: ignore
        elif state is Gst.State.PAUSED:
            offset = self.pipeline.get_start_time()
        else:
            return 0

        return 0 if offset == Gst.CLOCK_TIME_NONE else offset

    def _sync_pipeline_state(self):
        if not self._branches:
            # An audiomixer with no pads never prerolls, and it would leave the
            # next attached branch stuck; keep the pipeline down instead
            state = Gst.State.NULL
        elif self.playing:
            state = Gst.State.PLAYING
        else:
            state = Gst.State.PAUSED

        self.pipeline.set_state(state)

    def stop(self):
        """Release the pipeline, called on app shutdown"""
        self.pipeline.set_state(Gst.State.NULL)

    def _on_pipeline_error(self, _bus, message: Gst.Message):
        error, debug = message.parse_error()
        print(f"Error: GStreamer playback failed: {error.message}\n{debug}")

    def mute_vol_zero(self):
        for sound in self:
            if sound.saved_volume == 0:
                sound.playing = False

    def reset_volumes(self):
        self.emit("reset-volumes")

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

    def _inhibit(self, inhibit: bool):
        """
        Set suspension inhibition
        """
        app = Gtk.Application.get_default()
        if inhibit:
            if self._cookie:
                return

            self._cookie = app.inhibit(  # type: ignore
                None, Gtk.ApplicationInhibitFlags.SUSPEND, "Playback in progress"
            )
        elif self._cookie != 0:
            app.uninhibit(self._cookie)  # type: ignore
            self._cookie = 0

    def _on_playing(self, _player, _param):
        """
        Toggle pipeline state and suspension inhibition when playing
        """
        self._sync_pipeline_state()

        if Settings.get().inhibit_suspension:
            self._inhibit(self.playing)

    def _on_settings_inhibition(self, _settings: Settings, _key: str):
        """
        Toggle suspension inhibition when settings changes
        """
        if Settings.get().inhibit_suspension:
            self._inhibit(self.playing)
        else:
            self._inhibit(False)

    def _on_preset_changed(self, _settings, preset_id):
        self.emit("preset-changed", Preset(preset_id))

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

    def get_index(self, name: str) -> int | None:
        return self.get_by_name(name)[1]

    def get_by_index(self, index: int) -> GObject.Object:
        return self._sounds[index]
