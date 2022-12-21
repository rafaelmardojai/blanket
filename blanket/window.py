# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import os

from gettext import gettext as _
from gi.repository import Gio, GLib, GObject, Gtk, Adw

from blanket.settings import Settings
from blanket.sound import MainPlayer, SoundObject
from blanket.widgets import PlayPauseButton
from blanket.presets import PresetChooser

SOUNDS = [
    {
        'name': _('Nature'),
        'sounds': [
            {
                'name': 'rain',
                'title': _('Rain')
            },
            {
                'name': 'storm',
                'title': _('Storm')
            },
            {
                'name': 'wind',
                'title': _('Wind')
            },
            {
                'name': 'waves',
                'title': _('Waves')
            },
            {
                'name': 'stream',
                'title': _('Stream')
            },
            {
                'name': 'birds',
                'title': _('Birds')
            },
            {
                'name': 'summer-night',
                'title': _('Summer Night')
            }
        ]
    },
    {
        'name': _('Travel'),
        'sounds': [
            {
                'name': 'train',
                'title': _('Train')
            },
            {
                'name': 'boat',
                'title': _('Boat')
            },
            {
                'name': 'city',
                'title': _('City')
            }
        ]
    },
    {
        'name': _('Interiors'),
        'sounds': [
            {
                'name': 'coffee-shop',
                'title': _('Coffee Shop')
            },
            {
                'name': 'fireplace',
                'title': _('Fireplace')
            }
        ]
    },
    {
        'name': _('Noise'),
        'sounds': [
            {
                'name': 'pink-noise',
                'title': _('Pink Noise')
            },
            {
                'name': 'white-noise',
                'title': _('White Noise')
            }
        ]
    }
]


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/window.ui')
class BlanketWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'BlanketWindow'

    headerbar = Gtk.Template.Child()
    grid = Gtk.Template.Child()
    playpause_btn: PlayPauseButton = Gtk.Template.Child()
    menu = Gtk.Template.Child()
    volume = Gtk.Template.Child()
    presets_chooser: PresetChooser = Gtk.Template.Child()

    name_binding = None

    def __init__(self, mpris, **kwargs):
        super().__init__(**kwargs)

        # Set default window icon for window managers
        self.set_default_icon_name('com.rafaelmardojai.Blanket')

        # Main player & MPRIS server object
        self.mpris = mpris

        # Setup widgets
        self.setup()

    def setup(self):
        # Sounds model
        self.model = Gio.ListStore(item_type=SoundObject)

        # Setup grid
        selection = Gtk.NoSelection(model=self.model)
        factory = Gtk.BuilderListItemFactory.new_from_resource(
            None, '/com/rafaelmardojai/Blanket/grid-item.ui'
        )

        self.grid.props.factory = factory
        self.grid.props.model = selection
        self.grid.connect('activate', self._on_grid_activate)

        # Get volume scale adjustment
        vol_adjustment = self.volume.get_adjustment()
        # Bind volume scale value with main player volume
        vol_adjustment.bind_property('value', MainPlayer.get(),
                                     'volume',
                                     GObject.BindingFlags.BIDIRECTIONAL)
        # Set volume scale value on first run
        self.volume.set_value(MainPlayer.get().volume)

        # Wire playpause button
        MainPlayer.get().bind_property(
            'playing', self.playpause_btn, 'playing',
            GObject.BindingFlags.SYNC_CREATE
        )

        # Setup presets widgets
        self.setup_presets()
        # Setup included/saved sounds
        self.setup_sounds()

    def setup_presets(self):
        self.presets_chooser.connect('selected', self._on_preset_selected)
        self.update_title(self.presets_chooser.selected)
        self.mpris.update_title(self.presets_chooser.selected.name)

        items = self.presets_chooser.model.get_n_items()

    def setup_sounds(self):
        # Setup default sounds
        for g in SOUNDS:
            # Iterate sounds
            for s in g['sounds']:
                # Create a new SoundObject
                sound = SoundObject(s['name'], title=s['title'])
                self.model.append(sound)

        # Load saved custom audios
        for name, uri in Settings.get().custom_audios.items():
            # Create a new SoundObject
            sound = SoundObject(name, uri=uri, custom=True)
            self.model.append(sound)

    def open_audio(self):
        def on_response(_filechooser, _id):
            gfile = self.filechooser.get_file()
            if gfile:
                filename = gfile.get_path()
                name = os.path.basename(filename).split('.')[0]
                uri = gfile.get_uri()

                # Create a new SoundObject
                sound = SoundObject(name, uri=uri, custom=True)
                # Save to settings
                GLib.idle_add(Settings.get().add_custom_audio,
                              sound.name, sound.uri)
                # Add SoundObject to SoundsGroup
                self.model.append(sound)

        filters = {
            'Ogg': ['audio/ogg'],
            'FLAC': ['audio/flac'],
            'WAV': ['audio/x-wav', 'audio/wav'],
            'MP3': ['audio/mpeg'],
        }

        self.filechooser = Gtk.FileChooserNative.new(
            _('Open audio'),
            self,
            Gtk.FileChooserAction.OPEN,
            None,
            None)
        self.filechooser.connect('response', on_response)

        for f, mts in filters.items():
            audio_filter = Gtk.FileFilter()
            audio_filter.set_name(f)
            for mt in mts:
                audio_filter.add_mime_type(mt)
            self.filechooser.add_filter(audio_filter)

        response = self.filechooser.show()

    def update_title(self, preset):
        if self.name_binding is not None:
            self.name_binding.unbind()

        if preset.id != Settings.get().default_preset:
            self.name_binding = preset.bind_property(
                'name', self, 'title',
                GObject.BindingFlags.SYNC_CREATE
            )
        else:
            self.set_title(_('Blanket'))

    def _on_grid_activate(self, _grid, position):
        sound = self.model.get_item(position)
        sound.playing = not sound.playing

    def _on_preset_selected(self, _chooser, preset):
        MainPlayer.get().preset_changed()
        self.update_title(preset)
        self.mpris.update_title(preset.name)

    def _on_reset_volumes(self, _control, _preset):
        MainPlayer.get().reset_volumes()

    def _on_add_sound_clicked(self, _group):
        self.open_audio()
