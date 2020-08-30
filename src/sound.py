# sound.py
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

from gi.repository import GObject, Gst, Gtk, Handy

'''
SoundObject
Describe a sound with it's propeties
'''
class SoundObject(GObject.Object):

    def __init__(self, title, uri=None, icon=None, removable=False, **kwargs):
        super().__init__(**kwargs)

        resource_tmpl = 'resource:////com/rafaelmardojai/Blanket/sounds/{}.ogg'
        icon_tmpl = 'com.rafaelmardojai.Blanket-{}'

        self.removable = removable
        self.title = title
        self.name = title.replace(' ', '-').lower()
        self.uri = uri if uri else resource_tmpl.format(self.name)
        self.icon_name = icon if icon else icon_tmpl.format(self.name)


'''
SoundPlayer
Create and controll a GStreamer playbin with the given Sound

Based on Focusli JavaScript code
https://github.com/armonge/gnome-shell-extension-focusli
Copyright (C) 2017 Felipe Borges <felipeborges@gnome.org>

Ported to Python by Rafael Mardojai CM
'''
class SoundPlayer(object):

    def __init__(self, sound):
        self.sound = sound

        self.playbin = Gst.ElementFactory.make('playbin', self.sound.name)
        self.playbin.set_property('uri', self.sound.uri)

        self.prerolled = False
        playbin_bus = self.playbin.get_bus()
        playbin_bus.add_signal_watch()
        playbin_bus.connect("message", self._on_bus_message)

    def play(self):
        self.playbin.set_state(Gst.State.PLAYING)

    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)

    def set_volume(self, value):
        self.playbin.set_property('volume', value)
        state = self.playbin.get_state(Gst.State.NULL)

        if value == 0:
            self.pause()
        elif state is not Gst.State.PLAYING:
            self.play()

    def remove(self):
        self.playbin.set_state(Gst.State.NULL)
        self.playbin.unref()

    def _on_bus_message(self, bus, message):
        if message:
            if message.type is Gst.MessageType.SEGMENT_DONE:
                self.playbin.seek_simple(
                    Gst.Format.TIME,
                    Gst.SeekFlags.SEGMENT,
                    0
                )

            if message.type is Gst.MessageType.ASYNC_DONE:
                if not self.prerolled:
                    self.playbin.seek_simple(
                        Gst.Format.TIME,
                        Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT,
                        0
                    )
                    self.prerolled = True

            return True

