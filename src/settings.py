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

from gi.repository import GLib


class Settings(object):

    xdg_user_config_dir = GLib.get_user_config_dir()
    settings_file = os.path.join(xdg_user_config_dir, 'blanket', 'settings.json')

    def __init__(self):

        self.profile = 'Default'

        # Check if Settings file exists
        if not os.path.exists(self.settings_file):
            # Create empty settings dict
            self.settings = {}
            self.settings['profiles'] = {'Default': {}}
            self.settings['audios'] = {}

            # Write dict to file
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            self.save()
        else:
            with open(self.settings_file) as json_file:
                self.settings = json.load(json_file)

            if 'profiles' not in self.settings:
                settings['profiles'] = {'Default': {}}
                self.save()

            if 'audios' not in self.settings:
                settings['audios'] = {}
                self.save()

    def get_custom_audios(self):
        return self.settings['audios']

    def add_custom_audio(self, name, uri):
        if name in self.settings['audios']:
            # TODO: Do something
            pass
        else:
            self.settings['audios'][name] = uri
            self.save()

    def remove_custom_audio(self, name):
        if name in self.settings['audios']:
            del self.settings['audios'][name]
            profile = self.settings['profiles'][self.profile]
            if name in profile:
                del profile[name]
            self.save()
        else:
            # TODO: Do something
            pass

    def get_sound_volume(self, name):
        profile = self.settings['profiles'][self.profile]
        if name in profile:
            volume = profile[name]['volume']
            return volume if volume else None
        else:
            return None

    def set_sound_volume(self, name, volume):
        profile = self.settings['profiles'][self.profile]
        if name not in profile:
            profile[name] = {}
        profile[name]['volume'] = volume
        self.save()

    def save(self):
        with open(self.settings_file, 'w') as outfile:
            json.dump(self.settings, outfile, indent=2)

