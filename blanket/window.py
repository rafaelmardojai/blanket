# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import os

from gettext import gettext as _
from gi.repository import GLib, GObject, Gtk, Handy

from blanket.settings import Settings
from blanket.sound import SoundObject
from blanket.widgets import PlayPauseButton, SoundsGroup
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
class BlanketWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'BlanketWindow'

    headerbar = Gtk.Template.Child()
    scrolled_window = Gtk.Template.Child()
    box = Gtk.Template.Child()

    playpause_btn = Gtk.Template.Child()

    menu = Gtk.Template.Child()
    volume = Gtk.Template.Child()
    quit_revealer = Gtk.Template.Child()
    presets_btn = Gtk.Template.Child()
    new_preset_btn = Gtk.Template.Child()
    presets_chooser = Gtk.Template.Child()

    name_binding = None

    def __init__(self, mainplayer, **kwargs):
        super().__init__(**kwargs)

        # Set default window icon for window managers
        self.set_default_icon_name('com.rafaelmardojai.Blanket')

        # Main player
        self.mainplayer = mainplayer

        # Setup widgets
        self.setup()

    def setup(self):
        # Load dark theme
        gtk_settings = Gtk.Settings.get_default()
        gtk_settings.set_property(
            'gtk-application-prefer-dark-theme', Settings.get().dark_mode
        )

        # Get volume scale adjustment
        vol_adjustment = self.volume.get_adjustment()
        # Bind volume scale value with main player volume
        vol_adjustment.bind_property('value', self.mainplayer,
                                     'volume',
                                     GObject.BindingFlags.BIDIRECTIONAL)
        # Set volume scale value on first run
        self.volume.set_value(self.mainplayer.volume)

        # Wire playpause button
        self.mainplayer.bind_property(
            'playing', self.playpause_btn, 'playing',
            GObject.BindingFlags.SYNC_CREATE
        )

        # If background-playback enabled show quit action on menu
        self.quit_revealer.set_reveal_child(Settings.get().background)

        # Setup presets widgets
        self.setup_presets()
        # Setup included/saved sounds
        self.setup_sounds()
        self.setup_custom_sounds()

        # Show all widgets added to window
        self.show_all()

        # Get saved scroll position
        saved_scroll = Settings.get().scroll_position
        # Get scrolled window vertical adjustment
        self.vscroll = self.scrolled_window.get_vadjustment()
        # Set saved scroll to vertical adjustment
        self.vscroll.set_value(saved_scroll)

    def setup_presets(self):
        self.presets_chooser.connect('selected', self._on_preset_selected)
        self.update_title(self.presets_chooser.selected)

        self.presets_chooser.model.connect(
            'items-changed',
            self._on_presets_changed
        )
        items = self.presets_chooser.model.get_n_items()
        self.presets_btn.set_visible(items > 1)
        self.new_preset_btn.set_visible(items == 1)

    def setup_sounds(self):
        # Setup default sounds
        for g in SOUNDS:
            # Create a new SoundsGroup
            group = SoundsGroup(g['name'])
            # Iterate sounds
            for s in g['sounds']:
                # Create a new SoundObject
                sound = SoundObject(s['name'], title=s['title'],
                                    mainplayer=self.mainplayer)
                # Add SoundObject to SoundsGroup
                group.add(sound)

            # Add SoundsGroup to the window's main box
            self.box.pack_start(group, False, True, 0)

    def setup_custom_sounds(self):
        # Setup user custom sounds
        self.custom_sounds = SoundsGroup(_('Custom'), True)
        self.custom_sounds.connect('add-clicked', self._on_add_sound_clicked)
        self.box.pack_start(self.custom_sounds, False, True, 0)

        # Load saved custom audios
        for name, uri in Settings.get().custom_audios.items():
            # Create a new SoundObject
            sound = SoundObject(
                name, uri=uri, mainplayer=self.mainplayer, custom=True
            )
            # Add SoundObject to SoundsGroup
            self.custom_sounds.add(sound)

    def open_audio(self):
        filters = {
            'OGG': ['audio/ogg'],
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

        for f, mts in filters.items():
            audio_filter = Gtk.FileFilter()
            audio_filter.set_name(f)
            for mt in mts:
                audio_filter.add_mime_type(mt)
            self.filechooser.add_filter(audio_filter)

        response = self.filechooser.run()

        if response == Gtk.ResponseType.ACCEPT:
            filename = self.filechooser.get_filename()
            if filename:
                name = os.path.basename(filename).split('.')[0]
                uri = self.filechooser.get_uri()

                # Create a new SoundObject
                sound = SoundObject(
                    name, uri=uri, mainplayer=self.mainplayer, custom=True
                )
                # Save to settings
                GLib.idle_add(Settings.get().add_custom_audio,
                              sound.name, sound.uri)
                # Add SoundObject to SoundsGroup
                self.custom_sounds.add(sound)
                self.custom_sounds.show_all()

    def update_title(self, preset):
        if self.name_binding is not None:
            self.name_binding.unbind()

        if preset.id != Settings.get().default_preset:
            self.name_binding = preset.bind_property(
                'name', self.headerbar, 'title',
                GObject.BindingFlags.SYNC_CREATE
            )
        else:
            self.headerbar.set_title(_('Blanket'))

    def _on_preset_selected(self, _chooser, preset):
        self.mainplayer.preset_changed()
        self.update_title(preset)

    def _on_reset_volumes(self, _control, _preset):
        self.mainplayer.reset_volumes()

    def _on_presets_changed(self, model, _position, _removed, _added):
        items = model.get_n_items()
        self.presets_btn.set_visible(items > 1)
        self.new_preset_btn.set_visible(items == 1)

        if items == 1:
            self.menu.open_submenu('main')

    def _on_add_sound_clicked(self, _group):
        self.open_audio()
