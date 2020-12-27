# Copyright 2020 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gi.repository import Gtk

AUTHORS = [
    'Rafael Mardojai CM'
]

ARTISTS = {
    'Jakub Steiner' : [_('Rain'), _('Summer Night'), _('Storm'), _('Wind')]
}

SOUND_ARTISTS = {
    'alex36917': [_('Rain')],
    'Digifish music': [_('Storm')],
    'Falcet': [_('Boat')],
    'gezortenplotz': [_('City')],
    'gluckose': [_('Stream')],
    'Jorge Stolfi': [_('White Noise')],
    'kvgarlic': [_('Birds')],
    'Luftrum': [_('Waves')],
    'Omegatron': [_('Pink Noise')],
    'Stilgar': [_('Wind')],
    'vahid': [_('Train')],
    _('Unknown'): [_('Coffee Shop'), _('Fireplace'), _('Summer Night')],
}

SOUND_EDITORS = {
    'Porrumentzio': [_('Birds'), _('Rain'), _('Storm'), _('Waves'), _('Boat'), _('City')]
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
        sound_editors = self._get_credits_list(SOUND_EDITORS)

        # Set build version
        self.set_version(version)

        # Set authors list
        self.set_authors(AUTHORS)
        # Set artists list
        self.set_artists(artists)
        # Set sound artists list
        self.add_credit_section(_('Sounds by'), sound_artists)
        # Set sound editors list
        self.add_credit_section(_('Sounds edited by'), sound_editors)

    def _get_credits_list(self, _dict):
        l = ['']
        for k, vs in _dict.items():
            s = k + '\n	' + ', '.join(vs)
            l.append(s)
        return l

    def _on_about_response(self, dialog, response_id):
        self.destroy()

