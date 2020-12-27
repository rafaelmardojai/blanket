# widgets.py
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

from gi.repository import GLib, Gio, Gtk, Handy

from .sound import SoundObject, SoundPlayer
from .settings import Settings


'''
SoundRow
Create a widget to show, play and manage a Sound
'''
@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/sound-row.ui')
class SoundRow(Gtk.ListBoxRow):
    __gtype_name__ = 'SoundRow'

    box = Gtk.Template.Child()
    title = Gtk.Template.Child()
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
        if not playing:
            # If not playing set insensitive
            self.set_sensitive(False)
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
                                       'destructive-action')
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

    def remove(self, widget):
        # Remove audio from list
        self.model.remove(self.get_index())
        # Remove player
        self.player.remove()
        # Remove audio from settings
        self.settings.remove_custom_audio(self.sound.name)

    def _on_playing_changed(self, player, playing):
        playing = self.sound.mainplayer.get_property('playing')

        if playing:
            self.set_sensitive(True)
        else:
            self.set_sensitive(False)


'''
SoundsGroup
'''
class SoundsGroup(Gtk.Box):

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

