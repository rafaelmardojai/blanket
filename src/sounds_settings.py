# Copyright 2020 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import json

from gi.repository import Gio, GLib


class SoundsSettings(object):
    """
    Manages sounds settings
    """

    def __init__(self, gsettings):
        # New GSettings instance
        self.gsettings = gsettings
        # New dict with saved custom audios
        self.custom_audios = dict(self.gsettings.get_value('custom-audios'))
        # New dict with saved volume levels
        self.volume = dict(self.gsettings.get_value('sounds-volume'))

    def get_custom_audios(self):
        return self.custom_audios

    def add_custom_audio(self, name, uri):
        # Add the audio if the name is not already present
        # TODO: Do something if True
        if not name in self.custom_audios:
            # Add custom audio to audios dict, name: uri
            self.custom_audios[name] = uri

    def remove_custom_audio(self, name):
        # If name present in audios dict
        if name in self.custom_audios:
            # Remove sound from dict
            del self.custom_audios[name]

            if name in self.volume:
                # Remove audio also from volume dict
                del self.volume[name]

    def get_sound_volume(self, name):
        # If sound is set on volume dict
        if name in self.volume:
            volume = self.volume[name]
            return volume if volume else None
        else:
            return None

    def set_sound_volume(self, name, volume):
        # Set volume level to audio on volume dict
        self.volume[name] = volume

    def save_all(self):
        # Save custom audios
        self.gsettings.set_value('custom-audios', GLib.Variant('a{ss}', self.custom_audios))
        # Save sounds volume levels
        self.gsettings.set_value('sounds-volume', GLib.Variant('a{sd}', self.volume))


    def migrate_json(self):
        """
        Migrate old JSON settings
        Remove on Next release
        """
        xdg_user_config_dir = GLib.get_user_config_dir()
        json_settings_file = os.path.join(xdg_user_config_dir, 'blanket', 'settings.json')

        if os.path.exists(json_settings_file):
            try:
                with open(json_settings_file) as json_file:
                    self.json_settings = json.load(json_file)

                    for k, v in self.json_settings['audios'].items():
                        self.add_custom_audio(k, v)

                    for k, v in self.json_settings['profiles']['Default'].items():
                        print(k)
                        self.set_sound_volume(k, v['volume'])

                    os.remove(json_settings_file)

            except Exception:
                os.remove(json_settings_file)

