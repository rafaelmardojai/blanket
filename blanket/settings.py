# Copyright 2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Self
import uuid

from gi.repository import Gio, GLib, GObject


class Settings(Gio.Settings):
    _instance = None
    _presets_settings = {}

    __gsignals__ = {
        'preset-changed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    @classmethod
    def get(cls) -> Self:
        """Return an active instance of Settings."""
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance

    def __init__(self):
        super().__init__(schema_id='com.rafaelmardojai.Blanket')
        self.migrate_legacy_volumes()

    """ Autostart """

    @property
    def autostart(self) -> bool:
        return self.get_boolean('autostart')

    @autostart.setter
    def autostart(self, autostart: bool):
        self.set_boolean('autostart', autostart)

    """ Start in Pause """

    @property
    def start_paused(self) -> bool:
        return self.get_boolean('start-paused')

    @start_paused.setter
    def start_paused(self, paused: bool):
        self.set_boolean('start-paused', paused)

    """ Dark Mode """

    @property
    def dark_mode(self) -> bool:
        return self.get_boolean('dark-mode')

    @dark_mode.setter
    def dark_mode(self, dark: bool):
        self.set_boolean('dark-mode', dark)

    """ Sounds view scroll position """

    @property
    def scroll_position(self) -> float:
        return self.get_double('scroll-position')

    @scroll_position.setter
    def scroll_position(self, position: float):
        self.set_double('scroll-position', position)

    """ General volume level """

    @property
    def volume(self) -> float:
        return self.get_double('volume')

    @volume.setter
    def volume(self, volume: float):
        self.set_double('volume', volume)

    """ Playing state """

    @property
    def playing(self) -> bool:
        return self.get_boolean('playing')

    @playing.setter
    def playing(self, state: bool):
        self.set_boolean('playing', state)

    """ Background playing """

    @property
    def background(self) -> bool:
        return self.get_boolean('background-playback')

    @background.setter
    def background(self, background: bool):
        self.set_boolean('background-playback', background)

    """ Custom sounds """

    @property
    def custom_audios(self) -> dict[str, str]:
        return dict(self.get_value('custom-audios'))

    @custom_audios.setter
    def custom_audios(self, audios: dict[str, str]):
        self.set_value('custom-audios', GLib.Variant('a{ss}', audios))

    """ Custom sounds helper functions  """

    def add_custom_audio(self, name: str, uri: str):
        # Add the audio if the name is not already present
        if name not in self.custom_audios:
            saved_audios = self.custom_audios
            saved_audios[name] = uri
            self.custom_audios = saved_audios
        else:
            # TODO: Do something if True
            pass

    def remove_custom_audio(self, name: str):
        if name in self.custom_audios:
            saved_audios = self.custom_audios
            del saved_audios[name]
            self.custom_audios = saved_audios

            """
            # Also remove sound from volume dict
            if name in self.volume:
                del self.volume[name]
            """

    """ Presets """

    @property
    def presets(self) -> list[str]:
        return list(self.get_strv('presets'))

    @presets.setter
    def presets(self, presets: list[str]):
        self.set_strv('presets', presets)

    @property
    def active_preset(self) -> str:
        return self.get_string('active-preset')

    @active_preset.setter
    def active_preset(self, preset: str):
        self.set_string('active-preset', preset)
        self.emit('preset-changed', preset)

    @property
    def active_preset_name(self) -> str:
        return self.get_preset_name(self.active_preset)

    @property
    def default_preset(self) -> str:
        """Return the default preset ID."""
        return self.get_default_value('active-preset').get_string()  # type: ignore

    """ Presets helper functions  """

    def get_presets_dict(self) -> dict[str, str]:
        """Return the presets formatted as dict: ID => name."""
        presets_dict = {}
        for preset in self.presets:
            presets_dict[preset] = self.get_preset_name(preset)

        return presets_dict

    def add_preset(self, name: str) -> str:
        """Create a new Preset."""
        preset_id = str(uuid.uuid4())

        saved_presets = self.presets
        saved_presets.append(preset_id)
        self.presets = saved_presets

        # Set new preset name
        self.set_preset_name(preset_id, name)
        # Clone current preset to new
        current_volumes = self.get_preset_volumes(self.active_preset)
        current_mutes = self.get_preset_mutes(self.active_preset)
        self.set_preset_volumes(preset_id, current_volumes)
        self.set_preset_mutes(preset_id, current_mutes)

        return preset_id

    def remove_preset(self, preset_id: str) -> None | int:
        index = None

        if preset_id in self.presets:
            saved_presets = self.presets
            index = saved_presets.index(preset_id)
            saved_presets.remove(preset_id)
            self.presets = saved_presets

            # Remove settings instance
            if preset_id in self._presets_settings:
                del self._presets_settings[preset_id]

        # Return the index where the preset where positioned
        return index

    def get_preset_name(self, preset_id: str) -> str:
        settings = self.get_preset_settings(preset_id)
        return settings.get_string('visible-name')

    def set_preset_name(self, preset_id: str, name: str):
        preset = self.get_preset_settings(preset_id)
        preset.set_string('visible-name', name)
        preset.apply()  # Always apply changes on name change

    def get_preset_volumes(self, preset_id: str) -> dict[str, float]:
        settings = self.get_preset_settings(preset_id)
        return dict(settings.get_value('sounds-volume'))

    def set_preset_volumes(self, preset_id: str, volumes: dict[str, float]):
        settings = self.get_preset_settings(preset_id)
        settings.set_value('sounds-volume', GLib.Variant('a{sd}', volumes))

    def get_preset_mutes(self, preset_id: str) -> dict[str, bool]:
        settings = self.get_preset_settings(preset_id)
        return dict(settings.get_value('sounds-mute'))

    def set_preset_mutes(self, preset_id: str, mutes: dict[str, bool]):
        settings = self.get_preset_settings(preset_id)
        settings.set_value('sounds-mute', GLib.Variant('a{sb}', mutes))

    def get_preset_hide_inactive(self, preset_id: str) -> bool:
        settings = self.get_preset_settings(preset_id)
        return settings.get_boolean('hide-inactive')

    def set_preset_hide_inactive(self, preset_id: str, hide: bool):
        settings = self.get_preset_settings(preset_id)
        settings.set_boolean('hide-inactive', hide)

    """ Preset sound volume """

    def get_sound_volume(self, name: str):
        volumes = self.get_preset_volumes(self.active_preset)
        # If sound is set on volume dict
        if name in volumes:
            volume = volumes[name]
            if volume:
                return volume
        return 0.0

    def set_sound_volume(self, name: str, volume: float):
        saved_volumes = self.get_preset_volumes(self.active_preset)
        saved_volumes[name] = volume
        self.set_preset_volumes(self.active_preset, saved_volumes)

        if volume == 0:
            self.set_sound_mute(name, False)

    """ Preset sound mute """

    def get_sound_mute(self, name: str) -> bool:
        mutes = self.get_preset_mutes(self.active_preset)
        # If sound is set on mute dict
        if name in mutes:
            mute = mutes[name]
            return mute
        return True

    def set_sound_mute(self, name: str, mute: bool):
        saved_mutes = self.get_preset_mutes(self.active_preset)
        saved_mutes[name] = mute
        self.set_preset_mutes(self.active_preset, saved_mutes)

    """ Preset settings helper functions """

    def get_preset_settings(self, preset_id: str | None = None) -> Gio.Settings:
        """Get Preset Gio.Settings instance."""

        # By default return active preset
        if preset_id is None:
            preset_id = self.active_preset

        if preset_id not in self._presets_settings:
            path = self.get_property('path')
            if not path.endswith('/'):
                path += '/'
            path += preset_id + '/'
            self._presets_settings[preset_id] = Gio.Settings.new_with_path(
                'com.rafaelmardojai.Blanket.preset', path
            )
            # Set on ‘delay-apply’ mode so it only applies changes when we want
            self._presets_settings[preset_id].delay()

        return self._presets_settings[preset_id]

    def save_presets(self, preset_id: str | None = None):
        """Apply all the changes made to presets,
        or to a specific preset."""

        if preset_id is not None and preset_id in self._presets_settings:
            self._presets_settings[preset_id].apply()
        else:
            for key, settings in self._presets_settings.items():
                settings.apply()

    """ Legacy sounds volume """

    @property
    def legacy_sounds_volume(self) -> dict[str, float]:
        return dict(self.get_value('sounds-volume'))

    @legacy_sounds_volume.setter
    def legacy_sounds_volume(self, volumes_dict: dict[str, float]):
        self.set_value('sounds-volume', GLib.Variant('a{sd}', volumes_dict))

    def migrate_legacy_volumes(self):
        """Migrate legacy volumes to Default preset."""
        legacy_volumes = self.legacy_sounds_volume
        if legacy_volumes:
            self.set_preset_volumes(self.default_preset, legacy_volumes)
            self.legacy_sounds_volume = {}
