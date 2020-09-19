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

from gettext import gettext as _
from gi.repository import Gtk

AUTHORS = [
    'Rafael Mardojai CM'
]

ARTISTS = {
    'Jakub Steiner' : [_('Rain'), _('Storm'), _('Wind'), _('Summer Night')]
}

SOUND_ARTISTS = {
    'alex36917': [_('Rain')],
    'Digifish music': [_('Storm')],
    'Jorge Stolfi': [_('White Noise')],
    'kvgarlic': [_('Birds')],
    'Luftrum': [_('Waves')],
    'Omegatron': [_('Pink Noise')],
    'Stilgar': [_('Wind')],
    'vahid': [_('Train')]
    _('Unknown'): [_('Summer Night'), _('Coffee  Shop'), _('Fireplace')],
}

SOUND_EDITORS = {
    'Porrumentzio': [_('Birds'), _('Rain'), _('Storm'), _('Waves')]
}

@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/about.ui')
class AboutDialog(Gtk.AboutDialog):
    __gtype_name__ = 'AboutDialog'

    def __init__(self, version, **kwargs):
        super().__init__(**kwargs)
        # Connect "Close" button
        self.connect('response', self._on_about_response)

        artists = self._get_credits_list(ARTISTS)
        sound_artists = self._get_credits_list(SOUND_ARTISTS)

        # Set build version
        self.set_version(version)

        # Set authors list
        self.set_authors(AUTHORS)
        # Set artists list
        self.set_artists(artists)
        # Set sound artists list
        self.add_credit_section(_('Sounds by'), sound_artists)

    def _get_credits_list(self, _dict):
        l = ['']
        for k, vs in _dict.items():
            s = k + '\n	' + ', '.join(vs)
            l.append(s)
        return l

    def _on_about_response(self, dialog, response_id):
        self.destroy()

