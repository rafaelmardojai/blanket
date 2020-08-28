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

from gi.repository import Gio, Gtk, Handy

from .sound import SoundObject, SoundPlayer


'''
Sound
Create a widget to show, play and manage a Sound
'''
class Sound(Handy.ActionRow):

    def __init__(self, sound, **kwargs):
        super().__init__(**kwargs)

        self.set_activatable(False)
        self.set_selectable(False)
        # Set title
        self.set_title(sound.title)

        # Create a new SoundPlayer with the given Sound
        self.player = SoundPlayer(sound)

        # Create the box that will contain the player controls
        controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing = 6)
        self.add(controls)

        # Create a scale to controll the SoundPlayer volume
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.1)
        self.scale.set_draw_value(False)
        self.scale.props.expand = True
        self.scale.connect('value-changed', self.change_vol)
        controls.pack_start(self.scale, True, True, 0)

        # Create a icon for the Sound
        icon = Gtk.Image.new_from_icon_name(
            sound.icon_name, Gtk.IconSize.DIALOG)
        Gtk.StyleContext.add_class(icon.get_style_context(), 'sound-icon')
        icon.set_pixel_size(64)
        icon.props.margin_top = 6
        icon.props.margin_bottom = 6
        self.add_prefix(icon)

    def change_vol(self, scale):
        volume = scale.get_value()
        self.player.set_volume(volume)


'''
SoundsGroup
'''
class SoundsGroup(Gtk.Box):

    def __init__(self, title, **kwargs):
        super().__init__(**kwargs)

        self.props.orientation = Gtk.Orientation.VERTICAL
        self.props.spacing = 6

        self.model = Gio.ListStore.new(SoundObject)

        label = Gtk.Label(title, halign=Gtk.Align.START)
        Gtk.StyleContext.add_class(label.get_style_context(), 'h1')
        self.pack_start(label, False, False, 0)

        self.listbox = Gtk.ListBox()
        Gtk.StyleContext.add_class(self.listbox.get_style_context(), 'content')
        self.pack_start(self.listbox, True, False, 0)
        self.listbox.bind_model(self.model, self._create_sound_widget)

    def add(self, sound):
        self.model.append(sound)

    def _create_sound_widget(self, sound):
        widget = Sound(sound)
        return widget

