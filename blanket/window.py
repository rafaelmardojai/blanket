# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from urllib.parse import unquote, urlparse

from gettext import gettext as _
from gi.repository import Gio, GLib, GObject, Gtk, Adw

from blanket.define import RES_PATH, SOUNDS
from blanket.main_player import MainPlayer
from blanket.settings import Settings
from blanket.sound import Sound
from blanket.widgets import PlayPauseButton, PresetChooser, SoundItem, VolumeRow


@Gtk.Template(resource_path=f'{RES_PATH}/window.ui')
class BlanketWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'BlanketWindow'

    headerbar: Gtk.HeaderBar = Gtk.Template.Child()  # type: ignore
    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()  # type: ignore
    grid: Gtk.FlowBox = Gtk.Template.Child()  # type: ignore
    playpause_btn: PlayPauseButton = Gtk.Template.Child()  # type: ignore
    volumes: Gtk.Popover = Gtk.Template.Child()  # type: ignore
    volume: Gtk.Scale = Gtk.Template.Child()  # type: ignore
    volume_box: Gtk.Box = Gtk.Template.Child()  # type: ignore
    volume_list: Gtk.ListBox = Gtk.Template.Child()  # type: ignore
    presets_chooser: PresetChooser = Gtk.Template.Child()  # type: ignore
    labels_group: Gtk.SizeGroup = Gtk.Template.Child()  # type: ignore
    power_toast: Adw.Toast = Gtk.Template.Child()  # type: ignore

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set default window icon for window managers
        self.set_default_icon_name('com.rafaelmardojai.Blanket')

        self.setup_actions()
        # Setup widgets
        self.setup()
        # Setup volume
        self.setup_volume_menu()
        # Populate sounds
        self.populate_sounds()

    def setup(self):
        # Setup grid
        self.sounds_filter = Gtk.CustomFilter.new(
            match_func=self._hide_inactive_sounds_filter
        )
        self.sounds_model = Gtk.FilterListModel.new(
            model=MainPlayer.get(), filter=self.sounds_filter
        )
        self.grid.bind_model(self.sounds_model, self._create_sound_item)
        self.grid.connect('child-activated', self._on_sound_activate)

        # Wire playpause button
        MainPlayer.get().bind_property(
            'playing', self.playpause_btn, 'playing', GObject.BindingFlags.SYNC_CREATE
        )

        # Show preset chooser
        self.presets_chooser.props.visible = len(Settings.get().presets) > 1
        Settings.get().connect('changed::presets', self._on_presets_changed)

    def setup_actions(self):
        # Close window action
        action = Gio.SimpleAction.new('close', None)
        action.connect('activate', lambda _action, _param: self.close())
        self.add_action(action)

        # Hide non active sounds
        action = Gio.SimpleAction.new_stateful(
            'hide-inactive',
            None,
            Settings.get()
            .get_preset_settings(Settings.get().active_preset)
            .get_value('hide-inactive'),
        )
        action.connect('change-state', self._on_hide_non_active)
        self.add_action(action)

    def setup_volume_menu(self):
        # Get volume scale adjustment
        vol_adjustment = self.volume.get_adjustment()
        # Bind volume scale value with main player volume
        vol_adjustment.bind_property(
            'value', MainPlayer.get(), 'volume', GObject.BindingFlags.BIDIRECTIONAL
        )
        # Set volume scale value on first run
        self.volume.set_value(MainPlayer.get().volume)

        # Setup volume list
        self.volume_filter = Gtk.CustomFilter.new(match_func=lambda item: item.playing)
        model = Gtk.FilterListModel(model=MainPlayer.get(), filter=self.volume_filter)
        model.connect('items-changed', self._volume_model_changed)
        self.volume_box.props.visible = model.get_n_items() > 0
        self.volume_list.bind_model(model, self._create_vol_row)

        # Connect mainplayer preset-changed signal
        MainPlayer.get().connect_after('preset-changed', self._on_preset_changed)
        # Connect mainplayer reset-volumes signal
        MainPlayer.get().connect_after('reset-volumes', self._on_reset_volumes)

        self.volumes.connect('closed', self._volumes_popup_closed)

    def populate_sounds(self):
        """
        Populate default and saved sounds
        """

        # Self populate
        for g in SOUNDS:
            # Iterate sounds
            for s in g['sounds']:
                # Create a new Sound
                sound = Sound(s['name'], title=s['title'])
                MainPlayer.get().append(sound)

        # Load saved custom audios
        for name, uri in Settings.get().custom_audios.items():
            # Check if file actually exists
            path = unquote(urlparse(uri).path)
            if os.path.exists(path):
                # Create a new Sound
                sound = Sound(name, uri=uri, custom=True)
                MainPlayer.get().append(sound)
            else:
                Settings.get().remove_custom_audio(name)

                message = Adw.MessageDialog.new(
                    self,
                    _('Sound Automatically Removed'),
                    _(
                        'The {name} sound is no longer accessible, so it has been removed'
                    ).format(name=f'<b><i>{name}</i></b>'),
                )
                message.add_response('accept', _('Accept'))
                message.props.body_use_markup = True
                message.props.default_response = 'accept'
                message.props.close_response = 'accept'
                message.present()

    def open_audio(self):
        def on_response(_filechooser, _id):
            gfile = self.filechooser.get_file()
            if gfile:
                filename = gfile.get_path()
                if filename:
                    name = os.path.basename(filename).split('.')[0]
                    uri = gfile.get_uri()

                    # Create a new Sound
                    sound = Sound(name, uri=uri, custom=True)
                    # Save to settings
                    GLib.idle_add(
                        Settings.get().add_custom_audio, sound.name, sound.uri
                    )
                    # Add Sound to SoundsGroup
                    MainPlayer.get().append(sound)

        filters = {
            'Supported audio files': [
                'audio/ogg',
                'audio/flac',
                'audio/x-wav',
                'audio/wav',
                'audio/mpeg',
            ],
            'Ogg': ['audio/ogg'],
            'FLAC': ['audio/flac'],
            'WAV': ['audio/x-wav', 'audio/wav'],
            'MP3': ['audio/mpeg'],
        }

        self.filechooser = Gtk.FileChooserNative.new(  # type: ignore
            _('Open audio'), self, Gtk.FileChooserAction.OPEN, None, None
        )
        self.filechooser.connect('response', on_response)

        for f, mts in filters.items():
            audio_filter = Gtk.FileFilter()
            audio_filter.set_name(f)
            for mt in mts:
                audio_filter.add_mime_type(mt)
            self.filechooser.add_filter(audio_filter)

        self.filechooser.show()

    @Gtk.Template.Callback()
    def _on_narrow_window_apply(self, _breakpoint):
        if len(Settings.get().presets) > 1:
            self.headerbar.props.show_title = False

    @Gtk.Template.Callback()
    def _on_narrow_window_unapply(self, _breakpoint):
        self.headerbar.props.show_title = True

    def _hide_inactive_sounds_filter(self, item):
        return (
            not Settings.get().get_preset_hide_inactive(Settings.get().active_preset)
            or item.playing
        )

    def _on_hide_non_active(self, action, value: bool):
        action.set_state(value)
        Settings.get().set_preset_hide_inactive(Settings.get().active_preset, value)

        self.__update_filters()

    def _create_vol_row(self, sound):
        row = VolumeRow()

        row.volume = sound.saved_volume
        sound.bind_property(
            'saved_volume', row, 'volume', GObject.BindingFlags.BIDIRECTIONAL
        )

        sound.bind_property('title', row, 'title', GObject.BindingFlags.SYNC_CREATE)

        return row

    def _create_sound_item(self, sound):
        item = SoundItem()
        # Add label to size group
        self.labels_group.add_widget(item.label)

        if isinstance(sound, Sound):
            # Actual sound items
            item.sound = sound

            sound.bind_property(
                'playing', item, 'playing', GObject.BindingFlags.SYNC_CREATE
            )
            sound.bind_property(
                'title', item, 'title', GObject.BindingFlags.SYNC_CREATE
            )
            sound.bind_property(
                'icon_name', item, 'icon_name', GObject.BindingFlags.SYNC_CREATE
            )
        else:
            # Add new sound item
            item.title = _('Add…')
            item.icon_name = 'com.rafaelmardojai.Blanket-add'

        return item

    def _on_sound_activate(self, _grid, item):
        # If item sound is None, then it's the Add sound item
        if item.sound is not None:
            # Toggle sound playing state
            item.sound.playing = not item.sound.playing
            # Update volumes list
            self.__update_filters()
        else:
            # Open add sound file chooser
            self.open_audio()

    def _on_presets_changed(self, _settings, _key):
        self.presets_chooser.props.visible = len(Settings.get().presets) > 1

    def _on_preset_changed(self, _player, preset):
        self.__update_filters()

    def _on_reset_volumes(self, _player):
        self.__update_filters()

    def _volume_model_changed(self, model, _pos, _del, _add):
        # Hide volumes list if empty
        self.volume_box.props.visible = model.get_n_items() > 0

    def _volumes_popup_closed(self, _popover):
        # Disable sounds with volume = 0
        MainPlayer.get().mute_vol_zero()
        self.__update_filters()

    def _on_add_sound_clicked(self, _group):
        self.open_audio()

    def __update_filters(self):
        self.sounds_filter.changed(Gtk.FilterChange.DIFFERENT)
        self.volume_filter.changed(Gtk.FilterChange.DIFFERENT)

    def show_power_toast(self):
        self.toast_overlay.add_toast(self.power_toast)

    def hide_power_toast(self):
        self.power_toast.dismiss()
