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

    icon = Gtk.Template.Child()
    title = Gtk.Template.Child()
    controls = Gtk.Template.Child()
    volume = Gtk.Template.Child()
    #remove = Gtk.Template.Child()

    def __init__(self, sound, model, settings, label_group, **kwargs):
        super().__init__(**kwargs)

        # SoundObject
        self.sound = sound
        # Gio.ListStore
        self.model = model
        # Settings
        self.settings = settings

        # Create a new SoundPlayer with the given Sound
        self.player = SoundPlayer(self.sound)

        # Set icon for the Sound
        self.icon.set_from_icon_name(
            self.sound.icon_name, Gtk.IconSize.DIALOG)

        # Set title
        self.title.set_label(self.sound.title)
        # Add title to AddGtkSizeGroup for sound labels
        label_group.add_widget(self.title)

        # Connnect scale with volume function
        self.volume.connect('value-changed', self.change_vol)
        # Load saved volume
        saved_vol = self.settings.get_sound_volume(self.sound.name)
        if saved_vol and saved_vol > 0:
            self.volume.set_value(saved_vol)

        # Add a remove button if the sound is removable
        if self.sound.removable:
            # Create button
            remove = Gtk.Button(valign=Gtk.Align.CENTER)
            remove.connect('clicked', self.remove)
            self.controls.pack_end(remove, False, True, 0)
            # Add destructive-action CSS class
            Gtk.StyleContext.add_class(remove.get_style_context(), 'destructive-action')
            # Create button icon
            remove_icon = Gtk.Image.new_from_icon_name(
                'edit-delete-symbolic', Gtk.IconSize.MENU)
            remove.add(remove_icon)

    def change_vol(self, scale):
        volume = scale.get_value()
        self.player.set_volume(volume)
        # Save volume on settings
        GLib.idle_add(self.settings.set_sound_volume,
                      self.sound.name, volume)

    def remove(self, widget):
        self.model.remove(self.get_index())
        self.player.remove()
        # Remove audio from settings
        GLib.idle_add(self.settings.remove_custom_audio,
                      self.sound.name)


'''
SoundsGroup
'''
class SoundsGroup(Gtk.Box):

    def __init__(self, title, settings, label_group, **kwargs):
        super().__init__(**kwargs)

        # Setup box props
        self.props.orientation = Gtk.Orientation.VERTICAL
        self.props.spacing = 6

        # Settings
        self.settings = settings

        # GtkSizeGroup for sound labels
        self.label_group = label_group

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
        widget = SoundRow(sound, self.model, self.settings, self.label_group)
        return widget

