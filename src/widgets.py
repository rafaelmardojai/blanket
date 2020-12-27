# Copyright 2020 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GLib, Gio, Gtk, Handy

from .sound import SoundObject, SoundPlayer


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

    def __init__(self, sound, model, settings, **kwargs):
        super().__init__(**kwargs)

        # SoundObject
        self.sound = sound
        # Gio.ListStore
        self.model = model
        # Settings
        self.settings = settings

        # Get playing state
        playing = self.sound.mainplayer.get_property('playing')
        self.set_sensitive(playing)
        # Connect playing state signal
        self.sound.mainplayer.connect('notify::playing',
                                      self._on_playing_changed)

        # Create a new SoundPlayer
        self.player = SoundPlayer(self.sound)

        # Set title
        self.title.set_label(self.sound.title)

        # Connnect scale with volume function
        self.volume.connect('value-changed', self.change_vol)
        # Load saved volume
        saved_vol = self.settings.get_sound_volume(self.sound.name)
        if saved_vol and saved_vol > 0:
            self.volume.set_value(saved_vol)

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
            icon.set_pixel_size(64)
            Gtk.StyleContext.add_class(icon.get_style_context(),
                                       'icon-dropshadow')
            self.box.pack_start(icon, False, True, 0)
            self.box.child_set_property(icon, 'position', 0)

    def change_vol(self, scale):
        # Round volume value
        volume = round(scale.get_value(), 2)
        # Set player volume
        self.player.set_virtual_volume(volume)
        # Save volume on settings
        self.settings.set_sound_volume(self.sound.name, volume)
        # Toggle playing indicator
        if volume == 0:
            self.playing.set_reveal_child(False)
        else:
            self.playing.set_reveal_child(True)

    def remove(self, widget):
        # Remove audio from list
        self.model.remove(self.get_index())
        # Remove player
        self.player.remove()
        # Remove audio from settings
        self.settings.remove_custom_audio(self.sound.name)

    def _on_playing_changed(self, player, playing):
        playing = self.sound.mainplayer.get_property('playing')
        self.set_sensitive(playing)

class SoundsGroup(Gtk.Box):
    """
    SoundsGroup
    Group SoundRow with a title
    """

    def __init__(self, title, settings, **kwargs):
        super().__init__(**kwargs)

        # Setup box props
        self.props.orientation = Gtk.Orientation.VERTICAL
        self.props.spacing = 6

        # Settings
        self.settings = settings

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
        widget = SoundRow(sound, self.model, self.settings)
        return widget

