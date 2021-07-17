# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GLib, Gio, GObject, Gtk, Handy

from blanket.sound import SoundObject, SoundPlayer


class PlayPauseButton(Gtk.Button):
    __gtype_name__ = 'PlayPauseButton'

    playing = GObject.Property(type=bool, default=True)

    def __init__(self):
        super().__init__()

        self.pause_img = Gtk.Image.new_from_icon_name(
            'media-playback-pause-symbolic',
            Gtk.IconSize.MENU
        )
        self.play_img = Gtk.Image.new_from_icon_name(
            'media-playback-start-symbolic',
            Gtk.IconSize.MENU
        )

        self.connect('notify::playing', self._on_playing_changed)

    def _on_playing_changed(self, _object, _pspec):
        if self.playing:
            self.set_image(self.pause_img)
        else:
            self.set_image(self.play_img)


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/sound-row.ui')
class SoundRow(Gtk.ListBoxRow):
    __gtype_name__ = 'SoundRow'

    """
    SoundRow
    Widget to show, play and manage a sound
    """

    box = Gtk.Template.Child()
    title = Gtk.Template.Child()
    playing = Gtk.Template.Child()
    volume = Gtk.Template.Child()

    def __init__(self, sound, model):
        super().__init__()

        # SoundObject
        self.sound = sound
        # Gio.ListStore
        self.model = model

        # Get playing state
        self.volume.set_sensitive(self.sound.mainplayer.playing)
        # Connect playing state signal
        self.sound.mainplayer.connect(
            'notify::playing',
            self._on_playing_changed
        )
        # Connect mainplayer preset-changed signal
        self.sound.mainplayer.connect(
            'preset-changed',
            self._on_preset_changed
        )

        # Create a new SoundPlayer
        self.player = SoundPlayer(self.sound)

        # Set title
        self.title.set_label(self.sound.title)

        # Connect scale with volume function
        self.volume.connect('value-changed', self._on_volume_changed)
        # Load saved volume
        if self.sound.saved_volume and self.sound.saved_volume > 0:
            self.volume.set_value(self.sound.saved_volume)

        if self.sound.custom:
            # Add a remove button
            remove = Gtk.Button(valign=Gtk.Align.CENTER)
            remove.connect('clicked', self.remove)
            self.box.pack_end(remove, False, True, 0)
            # Add destructive-action CSS class
            Gtk.StyleContext.add_class(remove.get_style_context(),
                                       'image-button')
            # Create button icon
            remove_icon = Gtk.Image.new_from_icon_name(
                'edit-delete-symbolic', Gtk.IconSize.MENU)
            remove.add(remove_icon)
            # Compact widget
            self.box.props.margin_top = 0
            self.box.props.margin_bottom = 0
        else:
            # Set icon for the sound
            icon = Gtk.Image.new_from_icon_name(self.sound.icon_name,
                                                Gtk.IconSize.DIALOG)
            Gtk.StyleContext.add_class(icon.get_style_context(), 'sound-icon')
            icon.set_pixel_size(64)
            self.box.pack_start(icon, False, True, 0)
            self.box.child_set_property(icon, 'position', 0)

    def remove(self, _button):
        # Remove audio from list
        self.model.remove(self.get_index())
        # Remove player
        self.player.remove()
        # Remove audio from settings
        self.sound.remove()
    
    def _on_volume_changed(self, scale):
        # Round volume value
        volume = round(scale.get_value(), 2)
        # Set player volume
        self.player.set_virtual_volume(volume)
        # Save volume on settings
        self.sound.saved_volume = volume
        # Toggle playing indicator
        if volume == 0:
            self.playing.set_reveal_child(False)
            Gtk.StyleContext.remove_class(self.get_style_context(), 'playing')
        elif not self.playing.get_reveal_child():
            self.playing.set_reveal_child(True)
            Gtk.StyleContext.add_class(self.get_style_context(), 'playing')

    def _on_playing_changed(self, _player, _pspec):
        self.volume.set_sensitive(self.sound.mainplayer.playing)

    def _on_preset_changed(self, _player):
        if self.sound.saved_volume:
            self.volume.set_value(self.sound.saved_volume)
            self.player.play()
        else:
            self.volume.set_value(0.0)


class SoundsGroup(Gtk.Box):
    """
    SoundsGroup
    Group SoundRow with a title
    """

    def __init__(self, title):
        super().__init__()

        # Setup box props
        self.props.orientation = Gtk.Orientation.VERTICAL
        self.props.spacing = 6

        # Create GioListStore to store sounds
        self.model = Gio.ListStore.new(SoundObject)

        # Create group name label
        label = Gtk.Label(title, halign=Gtk.Align.START)
        Gtk.StyleContext.add_class(label.get_style_context(), 'h1')
        self.pack_start(label, False, False, 0)

        # Create group GtkListBox
        self.listbox = Gtk.ListBox()
        Gtk.StyleContext.add_class(self.listbox.get_style_context(), 'content')
        self.pack_start(self.listbox, True, False, 0)

        # Bind GtkListBox with GioListStore
        self.listbox.bind_model(self.model, self._create_sound_widget)

    def add(self, sound):
        self.model.append(sound)

    def _create_sound_widget(self, sound):
        widget = SoundRow(sound, self.model)
        return widget

