# Copyright 2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _


RES_PATH = '/com/rafaelmardojai/Blanket'

SOUNDS = [
    {
        'name': _('Nature'),
        'sounds': [
            {'name': 'rain', 'title': _('Rain')},
            {'name': 'storm', 'title': _('Storm')},
            {'name': 'wind', 'title': _('Wind')},
            {'name': 'waves', 'title': _('Waves')},
            {'name': 'stream', 'title': _('Stream')},
            {'name': 'birds', 'title': _('Birds')},
            {'name': 'summer-night', 'title': _('Summer Night')},
        ],
    },
    {
        'name': _('Travel'),
        'sounds': [
            {'name': 'train', 'title': _('Train')},
            {'name': 'boat', 'title': _('Boat')},
            {'name': 'city', 'title': _('City')},
        ],
    },
    {
        'name': _('Interiors'),
        'sounds': [
            {'name': 'coffee-shop', 'title': _('Coffee Shop')},
            {'name': 'fireplace', 'title': _('Fireplace')},
        ],
    },
]

NOISES = [
    {'name': 'pink-noise', 'title': _('Pink Noise')},
    {'name': 'white-noise', 'title': _('White Noise')},
]

AUTHORS = ['Rafael Mardojai CM']

ARTISTS = {'Jakub Steiner': [_('Sounds icons')], 'Rafael Mardojai CM': [_('App icon')]}

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
    'stephan': [_('Coffee Shop')],
    'Omegatron': [_('Pink Noise')],
    'felix.blume': [_('Wind')],
    'SDLx': [_('Train')],
}

SOUND_EDITORS = {
    'Porrumentzio': [
        _('Birds'),
        _('Rain'),
        _('Storm'),
        _('Waves'),
        _('Boat'),
        _('City'),
        _('Wind'),
    ]
}
