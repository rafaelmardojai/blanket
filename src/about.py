# about.py
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

from gi.repository import Gtk

AUTHORS = [
    'Rafael Mardojai CM',
    ''
]

ARTISTS = [
'''Jakub Steiner:
    rain, storm, wind and summer-night icons''',
''
]

SOUND_ARTISTS = [
'''Digifish music:
    storm sound''',
'''JPolito:
    rain sound''',
'''Mike Koenig:
    white-noise sound''',
'''Omegatron:
    pink-noise sound''',
'''Stilgar:
    wind sound''',
'''Unknown:
    summer-night, coffee-shop and fireplace sounds'''
]

@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/about.ui')
class AboutDialog(Gtk.AboutDialog):
    __gtype_name__ = 'AboutDialog'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_authors(AUTHORS)
        self.set_artists(ARTISTS)

        self.add_credit_section(_('Sounds by'), SOUND_ARTISTS)

