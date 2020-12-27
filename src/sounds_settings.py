# settings.py
#
# Copyright 2020 Rafael Mardojai CM
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import json

from gi.repository import GLib, Gio


class SoundsSettings(object):
    """
    Manages sounds settings
    """

    def __init__(self):
        # New GSettings instance
        self.gsettings = Gio.Settings.new('com.rafaelmardojai.Blanket')
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
        '''
        Migration
        Remove on Next release
        '''
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

