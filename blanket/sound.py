# Copyright 2020 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GLib, GObject, Gst

from blanket.audio import LoopBin, NoiseBin, SoundBin
from blanket.define import RES_PATH
from blanket.main_player import MainPlayer
from blanket.settings import Settings

# Seconds an inaudible sound keeps its decoder before it is released
DETACH_DELAY = 5


class Sound(GObject.Object):
    """
    Describe a sound with it's properties
    """

    __gtype_name__ = "Sound"

    playing: bool = GObject.Property(type=bool, default=False)  # type: ignore
    title: str = GObject.Property(type=str)  # type: ignore
    icon_name: str = GObject.Property(type=str)  # type: ignore
    error_message: str = GObject.Property(type=str)  # type: ignore

    def __init__(
        self,
        name: str,
        uri: str | None = None,
        title: str | None = None,
        noise: bool | None = False,
        custom: bool | None = False,
        failed: bool = False,
        error_message: str | None = None,
    ):
        super().__init__()

        resource = f"resource:{RES_PATH}/sounds/{name}.ogg"
        icon = "blanket-{}-symbolic"

        self._failed = failed

        # Internal player
        self._player: SoundBin | None = None
        self._mixer_pad: Gst.Pad | None = None
        self._detach_id: int = 0
        self._removed = False

        # Sound properties
        self.name = name
        self.uri = uri if uri else resource
        self.error_message = error_message or ""
        self.title = title if title else name
        self.icon_name = icon.format("sound-wave" if custom else name)
        self.noise = noise
        self.custom = custom

        # Playing state
        self.connect("notify::playing", self._playing_changed)
        if not self.saved_mute and not self.failed:
            self.playing = True

        # Connect mainplayer preset-changed signal
        self._preset_hdlr = MainPlayer.get().connect(
            "preset-changed", self._on_preset_changed
        )
        # Connect mainplayer reset-volumes signal
        self._reset_hdlr = MainPlayer.get().connect(
            "reset-volumes", self._on_reset_volumes
        )
        # Connect mainplayer playing signal
        self._main_player_playing_hdlr = MainPlayer.get().connect(
            "notify::playing", self._on_main_player_playing
        )

    @GObject.Property(type=float)
    def saved_volume(self) -> float:
        return Settings.get().get_sound_volume(self.name)

    @saved_volume.setter
    def saved_volume(self, volume: float):
        if self._removed:
            return

        volume = round(volume, 2)

        if self._player:
            self._player.volume = volume

        Settings.get().set_sound_volume(self.name, volume)

        if volume != 0 and not self.playing:
            self.playing = True

    @property
    def saved_mute(self) -> bool:
        return Settings.get().get_sound_mute(self.name)

    @saved_mute.setter
    def saved_mute(self, mute: bool):
        Settings.get().set_sound_mute(self.name, mute)

    @GObject.Property(type=bool, default=False)
    def failed(self) -> bool:
        return self._failed

    @failed.setter
    def failed(self, value: bool):
        self._failed = value

        if self.playing and value:
            self.playing = False

    def remove(self):
        """Remove sound if it is custom"""
        if self.custom:
            self._removed = True
            self._cancel_detach()
            self._detach()

            # A removed sound still reachable from a signal closure would
            # otherwise come back to life on the next preset change.
            MainPlayer.get().disconnect(self._preset_hdlr)
            MainPlayer.get().disconnect(self._reset_hdlr)
            MainPlayer.get().disconnect(self._main_player_playing_hdlr)

            Settings.get().remove_custom_audio(self.name)

    def _playing_changed(self, _object, _pspec):
        if self._removed:
            return

        # Toggle player mute state
        if self.playing:
            if self.saved_volume == 0:
                self.saved_volume = 0.5

            if self._player:
                self._player.volume = self.saved_volume

        self.saved_mute = not self.playing  # Save playing state
        self._update_playback()

    def _on_preset_changed(self, _player, _preset):
        self.notify("saved_volume")
        self.playing = not self.saved_mute

    def _on_reset_volumes(self, _player):
        self.saved_volume = 0.0
        self.playing = False

    def _on_main_player_playing(self, _object, _pspec):
        self._update_playback()

    """
    Branch handling
    """

    def release_now(self):
        """Tear the branch down without waiting for the stream to go idle"""
        self._cancel_detach()
        self._detach()

    def play_now(self):
        """Play the sound immediately"""
        self._playback_up()

    def _update_playback(self):
        """Update playback state on sound and main player state"""
        if self.playing and MainPlayer.get().playing:
            if self.saved_volume > 0:
                self._playback_up()
                return

        if MainPlayer.get().playing:
            self._playback_down()

    def _playback_up(self):
        if self.failed:
            return

        self._cancel_detach()
        if self._player is None:
            self._attach()

        if self._player:
            self._player.volume = self.saved_volume

    def _playback_down(self):
        if self._player is not None:
            self._player.volume = 0
            self._schedule_detach()

    def _schedule_detach(self):
        if self._player is None or self._detach_id:
            return

        self._detach_id = GLib.timeout_add_seconds(DETACH_DELAY, self._detach_timeout)

    def _cancel_detach(self):
        if self._detach_id:
            GLib.source_remove(self._detach_id)
            self._detach_id = 0

    def _detach_timeout(self):
        self._detach_id = 0
        self._detach()
        return GLib.SOURCE_REMOVE

    def _detach(self):
        if self._player is None or self._mixer_pad is None:
            return

        MainPlayer.get().detach_sound_bin(self._player, self._mixer_pad)

        self._mixer_pad = None
        self._player = None

    def _attach(self):
        if self._player is not None:
            return

        if self.noise:
            self._player = NoiseBin(self.name)
        else:
            self._player = LoopBin(self.uri)

        self._mixer_pad = MainPlayer.get().attach_sound_bin(self._player)
