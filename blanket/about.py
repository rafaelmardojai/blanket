# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gi.repository import Gtk

AUTHORS = [
    'Rafael Mardojai CM'
]

ARTISTS = {
    'Jakub Steiner': [_('Sounds icons')],
    'Rafael Mardojai CM': [_('App icon')]
}

SOUND_ARTISTS = {
    'alex36917': [_('Rain')],
    'Digifish music': [_('Storm')],
    'ezwa': [_('Fireplace')],
    'Falcet': [_('Boat')],
    'gezortenplotz': [_('City')],
    'gluckose': [_('Stream')],
    'Jorge Stolfi': [_('White Noise')],
    'kvgarlic': [_('Birds')],
    'Lisa Redfern': [_('Summer Night')],
    'Luftrum': [_('Waves')],
    'Omegatron': [_('Pink Noise')],
    'felix.blume': [_('Wind')],
    'vahid': [_('Train')],
    _('Unknown'): [_('Coffee Shop'), _('Fireplace'), _('Summer Night')],
}

SOUND_EDITORS = {
    'Porrumentzio': [
        _('Birds'), _('Rain'), _('Storm'), _('Waves'), _('Boat'), _('City'), _('Wind')]
}


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/about.ui')
class AboutDialog(Gtk.AboutDialog):
    __gtype_name__ = 'AboutDialog'

    def __init__(self, version):
        super().__init__()
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

    def _get_credits_list(self, dict_):
        credits_list = ['']
        for k, vs in dict_.items():
            s = k + '\n	' + ', '.join(vs)
            credits_list.append(s)
        return credits_list

    def _on_about_response(self, _dialog, _response_id):
        self.destroy()
