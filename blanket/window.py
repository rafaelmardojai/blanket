# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import os

from gettext import gettext as _
from gi.repository import GLib, GObject, Gtk, Handy

from blanket.settings import Settings
from blanket.sound import SoundObject
from blanket.widgets import PlayPauseButton, SoundsGroup
from blanket.presets import PresetChooser, PresetControl

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
    flap = Gtk.Template.Child()
    scrolled_window = Gtk.Template.Child()
    box = Gtk.Template.Child()

    playpause_btn = Gtk.Template.Child()
    volume = Gtk.Template.Child()
    quit_revealer = Gtk.Template.Child()

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
        self.volume.set_value(self.mainplayer.get_property('volume'))

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
        self.presets = PresetChooser(self)
        self.flap.set_flap(self.presets)

        self.presets_chooser = PresetControl(self)
        self.headerbar.pack_start(self.presets_chooser)
        self.headerbar.child_set_property(self.presets_chooser, 'position', 0)

        self.presets.connect('selected', self._on_preset_selected)

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
        self.custom_sounds = SoundsGroup(_('Custom'))
        self.box.pack_start(self.custom_sounds, False, True, 0)

        # Add sound button row
        add_row = Gtk.ListBoxRow()
        add_row.set_selectable(False)
        add_row_box = Gtk.Box(
            height_request=34
        )
        add_row.add(add_row_box)
        add_row_icon = Gtk.Image.new_from_icon_name(
            'list-add-symbolic',
            Gtk.IconSize.MENU
        )
        add_row_box.pack_start(add_row_icon, True, True, 0)
        self.custom_sounds.listbox.add(add_row)
        self.custom_sounds.listbox.connect('row-activated', self.open_audio)

        # Load saved custom audios
        for name, uri in Settings.get().custom_audios.items():
            # Create a new SoundObject
            sound = SoundObject(
                name, uri=uri, mainplayer=self.mainplayer, custom=True
            )
            # Add SoundObject to SoundsGroup
            self.custom_sounds.add(sound)

    def open_audio(self, _widget=None, _row=None):

        filters = {
            'OGG': ['audio/ogg'],
            'FLAC': ['audio/x-flac'],
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

    def _on_preset_selected(self, _chooser, _preset):
        self.mainplayer.preset_changed()
