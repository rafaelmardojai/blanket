# Copyright 2020 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import uuid

from gi.repository import Gio, GLib


class Settings(Gio.Settings):
    instance = None

    def __init__(self):
        Gio.Settings.__init__(self)

    @staticmethod
    def new():
        """Create a new instance of Settings."""
        g_settings = Gio.Settings.new('com.rafaelmardojai.Blanket')
        g_settings.__class__ = Settings
        return g_settings

    @staticmethod
    def get():
        """Return an active instance of Settings."""
        if Settings.instance is None:
            Settings.instance = Settings.new()
            Settings.instance.migrate_legacy_volumes()

        return Settings.instance

    """ Sounds view scroll position """
    @property
    def scroll_position(self):
        return self.get_double('scroll-position')

    @scroll_position.setter
    def scroll_position(self, position):
        self.set_double('scroll-position', position)

    """ General volume level """
    @property
    def volume(self):
        return self.get_double('volume')

    @volume.setter
    def volume(self, volume):
        self.set_double('volume', volume)

    """ Playing state """
    @property
    def playing(self):
        return self.get_boolean('playing')

    @playing.setter
    def playing(self, state):
        self.set_boolean('playing', state)

    """ Custom sounds """
    @property
    def custom_audios(self):
        return dict(self.get_value('custom-audios'))

    @custom_audios.setter
    def custom_audios(self, audios):
        self.set_value('custom-audios', GLib.Variant('a{ss}', audios))

    """ Custom sounds helper functions  """
    def add_custom_audio(self, name, uri):
        # Add the audio if the name is not already present
        if name not in self.custom_audios:
            saved_audios = self.custom_audios
            saved_audios[name] = uri
            self.custom_audios = saved_audios
        else:
            # TODO: Do something if True
            pass

    def remove_custom_audio(self, name):
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
    def presets(self):
        return list(self.get_value('presets'))

    @presets.setter
    def presets(self, presets):
        self.set_value('presets', GLib.Variant('as', presets))

    @property
    def active_preset(self):
        return self.get_string('active-preset')

    @active_preset.setter
    def active_preset(self, preset):
        self.set_string('active-preset', preset)

    @property
    def active_preset_name(self):
        return self.get_preset_name(self.active_preset)

    @property
    def default_preset(self):
        """ Return the default preset ID. """
        return self.get_default_value('active-preset').get_string()

    """ Presets helper functions  """
    def get_presets_dict(self):
        """ Return the presets formated as dict: ID => name. """
        presets_dict = {}
        for preset in self.presets:
            presets_dict[preset] = self.get_preset_name(preset)

        return presets_dict

    def add_preset(self, name):
        """ Create a new Preset. """
        preset_id = str(uuid.uuid4())

        saved_presets = self.presets
        saved_presets.append(preset_id)
        self.presets = saved_presets

        self.set_preset_name(preset_id, name)

        return preset_id

    def remove_preset(self, preset_id):
        if preset_id in self.presets:
            saved_presets = self.presets
            saved_presets.remove(preset_id)
            self.presets = saved_presets

    def get_preset_name(self, preset_id):
        settings = self.get_preset_settings(preset_id)
        return settings.get_string('visible-name')

    def set_preset_name(self, preset_id, name):
        preset = self.get_preset_settings(preset_id)
        preset.set_string('visible-name', name)

    def get_preset_volumes(self, preset_id):
        settings = self.get_preset_settings(preset_id)
        return dict(settings.get_value('sounds-volume'))

    def set_preset_volumes(self, preset_id, volumes):
        settings = self.get_preset_settings(preset_id)
        settings.set_value('sounds-volume', GLib.Variant('a{sd}', volumes))

    def get_preset_settings(self, preset_id):
        """ Get Preset Gio.Settings instance. """
        path = self.get_property('path')
        if not path.endswith('/'):
            path += '/'
        path += preset_id + '/'

        return Gio.Settings('com.rafaelmardojai.Blanket.preset', path)

    """ Sounds volume """
    def get_sound_volume(self, name):
        volumes = self.get_preset_volumes(self.active_preset)
        # If sound is set on volume dict
        if name in volumes:
            volume = volumes[name]
            return volume if volume else None
        else:
            return None

    def set_sound_volume(self, name, volume):
        saved_volumes = self.get_preset_volumes(self.active_preset)
        saved_volumes[name] = volume
        self.set_preset_volumes(self.active_preset, saved_volumes)

    """ Legacy sounds volume """
    @property
    def legacy_sounds_volume(self):
        return dict(self.get_value('sounds-volume'))

    @legacy_sounds_volume.setter
    def legacy_sounds_volume(self, volumes_dict):
        self.set_value('sounds-volume', GLib.Variant('a{sd}', volumes_dict))

    def migrate_legacy_volumes(self):
        """ Migrate legacy volumes to Default preset. """
        legacy_volumes = self.legacy_sounds_volume
        if legacy_volumes:
            self.set_preset_volumes(self.default_preset, legacy_volumes)
            self.legacy_sounds_volume = {}
