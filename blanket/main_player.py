# Copyright 2020 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING, Iterator, Self

from gi.repository import Gio, GLib, GObject, Gst, GstAudio, Gtk

from blanket.preset import Preset
from blanket.settings import Settings

if TYPE_CHECKING:
    from blanket.sound import Sound


class MainPlayer(GObject.GObject, Gio.ListModel):
    """
    Blanket's omnipresent sounds player

    It also implements Gio.ListModel and stores the app sound list.
    """

    _instance = None
    _cookie = 0
    _sounds: list["Sound"] = []  # Sound list

    __gtype_name__ = "MainPlayer"
    __gsignals__ = {
        "preset-changed": (GObject.SIGNAL_RUN_FIRST, None, (GObject.Object,)),
        "reset-volumes": (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    playing: bool = GObject.Property(type=bool, default=False)  # type: ignore
    volume: float = GObject.Property(type=float, default=0)  # type: ignore

    @classmethod
    def get(cls) -> Self:
        """Return an active instance of MainPlayer."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.connect("notify::playing", self._on_playing)
        Settings.get().connect("preset-changed", self._on_preset_changed)
        Settings.get().connect(
            "changed::inhibit-suspension", self._on_settings_inhibition
        )

        self._setup_pipeline()

    def _setup_pipeline(self):
        """
        Set up the single pipeline shared by every sound

        Each playing sound is a branch feeding the mixer, so all of them are
        decoded into one stream and go out through a single audio sink.
        """
        self._branches: int = 0
        self._detaching: set[Gst.Bin] = set()

        self.pipeline = Gst.Pipeline.new("blanket")
        self.mixer = Gst.ElementFactory.make("audiomixer", "mixer")
        convert = Gst.ElementFactory.make("audioconvert", None)
        resample = Gst.ElementFactory.make("audioresample", None)
        volume = Gst.ElementFactory.make("volume", None)
        sink = Gst.ElementFactory.make("autoaudiosink", None)

        if not self.mixer or not convert or not resample or not volume or not sink:
            raise RuntimeError("Could not create the GStreamer playback elements")

        for element in (self.mixer, convert, resample, volume, sink):
            self.pipeline.add(element)

        self.mixer.link(convert)
        convert.link(resample)
        resample.link(volume)
        volume.link(sink)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_pipeline_error)

        # Make main player control sink volume
        volume.bind_property(
            "volume",
            self,
            "volume",
            GObject.BindingFlags.BIDIRECTIONAL,
            self._vol_to_gst,
            self._vol_to_ui,
        )

    def _vol_to_gst(self, _bind, from_val: float) -> float:
        return GstAudio.StreamVolume.convert_volume(
            GstAudio.StreamVolumeFormat.LINEAR,
            GstAudio.StreamVolumeFormat.CUBIC,
            from_val,
        )

    def _vol_to_ui(self, _bind, from_val: float) -> float:
        return GstAudio.StreamVolume.convert_volume(
            GstAudio.StreamVolumeFormat.CUBIC,
            GstAudio.StreamVolumeFormat.LINEAR,
            from_val,
        )

    def attach_sound_bin(
        self,
        sound_bin: Gst.Bin,
    ) -> Gst.Pad | None:
        """Attach a sound player to the pipeline mixer."""
        if self.mixer is None:
            return None

        self.pipeline.add(sound_bin)

        mixer_pad = self.mixer.request_pad_simple("sink_%u")
        src_pad = sound_bin.get_static_pad("src")

        if mixer_pad is None or src_pad is None:
            return None

        # Shift the branch to where the mixer already is, or it would produce
        # buffers the mixer considers long past and drops.
        src_pad.set_offset(self._get_branch_offset())
        src_pad.link(mixer_pad)

        self._branches += 1  # Increment branch count
        self._sync_pipeline_state()
        sound_bin.sync_state_with_parent()

        return mixer_pad

    def detach_sound_bin(self, sound_bin: Gst.Bin, mixer_pad: Gst.Pad) -> None:
        """Detach a sound player from the pipeline mixer."""

        # A branch that is being unlinked while it still runs reports a
        # not-linked error on its way out; that one is expected.
        self._detaching.add(sound_bin)

        state: Gst.State = self.pipeline.get_state(0).state  # type: ignore
        if state is not Gst.State.PLAYING:
            # Nothing is streaming, so a blocking probe would never be called,
            # just destroy the branch immediately.
            self._destroy_branch(sound_bin, mixer_pad)
            return

        # Block the branch before tearing it down, so the mixer never sees a
        # half-removed pad.
        if pad := sound_bin.get_static_pad("src"):
            pad.add_probe(
                Gst.PadProbeType.IDLE,
                lambda _pad, _info: self._on_branch_blocked(sound_bin, mixer_pad),
            )

    def _on_branch_blocked(self, sound_bin: Gst.Bin, mixer_pad: Gst.Pad):
        # States cannot be changed from a streaming thread
        GLib.idle_add(self._destroy_branch, sound_bin, mixer_pad)
        return Gst.PadProbeReturn.REMOVE

    def _destroy_branch(self, sound_bin: Gst.Bin, mixer_pad: Gst.Pad):
        """Destroy a sound branch and remove it from the pipeline."""
        if self.mixer is None:
            return

        # Stop the branch before unlinking it, so it does not push into a pad
        # that is already gone.
        sound_bin.set_state(Gst.State.NULL)
        if pad := sound_bin.get_static_pad("src"):
            pad.unlink(mixer_pad)

        self.mixer.release_request_pad(mixer_pad)
        self.pipeline.remove(sound_bin)

        self._detaching.discard(sound_bin)  # Remove from detaching set
        self._branches -= 1  # Decrement branch count
        self._sync_pipeline_state()

        return GLib.SOURCE_REMOVE

    def _get_branch_offset(self) -> int:
        """
        A branch about to be attached has to be shifted to match the mixer's
        current position.

        The mixer works in running time, so a branch joining a pipeline that
        already advanced would be mixed in the past and dropped.
        """
        if not self.mixer:
            return 0

        state: Gst.State = self.pipeline.get_state(0).state  # type: ignore

        if state is Gst.State.PLAYING:
            offset = self.mixer.get_current_running_time()
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
        if self._owner(message.src, self._detaching) is not None:
            return  # Branch on its way out of the pipeline

        error, debug = message.parse_error()
        print(f"Error: GStreamer playback failed: {error.message}\n{debug}")

        # Every sound shares this pipeline, so a single unreadable file would
        # otherwise take the whole mix down with it
        sound = self._sound_of(message.src)
        if sound is not None:
            sound.playing = False

        GLib.idle_add(self._recover)

    def _recover(self):
        """
        Bring the pipeline back after an error

        GStreamer will not resume a pipeline that reported one, so it has to go
        through NULL and have the remaining sounds attached again.
        """
        # The whole pipeline goes down first: tearing the branches down one by
        # one would block on threads the stalled mixer still holds
        self.pipeline.set_state(Gst.State.NULL)

        for sound in self:
            sound.release_now()

        self._branches = 0
        self._detaching.clear()

        for sound in self:
            if sound.playing and sound.saved_volume > 0:
                sound.play_now()

        return GLib.SOURCE_REMOVE

    def _sound_of(self, element: Gst.Object | None):
        """Find the sound a pipeline element belongs to, if any"""
        branches = {}
        for sound in self:
            player = getattr(sound, "_player", None)
            sound_bin = player._bin if player else None
            if sound_bin is not None:
                branches[sound_bin] = sound

        return self._owner(element, branches)

    def _owner(self, element: Gst.Object | None, branches):
        """Walk up from an element to the branch it lives in"""
        while element is not None:
            if element in branches:
                return branches[element] if isinstance(branches, dict) else element
            element = element.get_parent()

        return None

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
        app: Gtk.Application | None = Gtk.Application.get_default()  # type: ignore

        if not app:
            return

        if inhibit:
            if self._cookie:
                return

            self._cookie = app.inhibit(
                None, Gtk.ApplicationInhibitFlags.SUSPEND, "Playback in progress"
            )
        elif self._cookie != 0:
            app.uninhibit(self._cookie)
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
    """

    def __iter__(self) -> Iterator[Sound]:
        return iter(self._sounds)

    def do_get_item(self, position: int) -> GObject.Object:
        return self._sounds[position]

    def do_get_item_type(self) -> type:
        return GObject.Object

    def do_get_n_items(self) -> int:
        return len(self._sounds)

    def append(self, sound: "Sound"):
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
