# window.py
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

from gi.repository import Gtk, Gio, Handy

from .sound import Sound, SoundWidget


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/window.ui')
class BlanketWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'BlanketWindow'

    default_list = Gtk.Template.Child()

    sounds = [
        'Rain',
        'Wind'
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.model = Gio.ListStore.new(Sound)
        self.default_list.bind_model(self.model, self._create_sound_widget)

        for s in self.sounds:
            sound = Sound(s)
            self.model.append(sound)

        self.default_list.show_all()

    def _create_sound_widget(self, sound):
        widget = SoundWidget(sound)
        return widget

