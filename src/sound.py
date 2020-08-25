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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.# window.py

from gi.repository import GObject, Gst, Gtk, Handy

'''
Sound object
Describe a sound with it's propeties
'''
class Sound(GObject.Object):

    def __init__(self, title, uri=None, icon=None, **kwargs):
        super().__init__(**kwargs)

        resource_tmpl = 'resource:////com/rafaelmardojai/Blanket/sounds/{}.ogg'
        icon_tmpl = 'com.rafaelmardojai.Blanket-{}'

        self.title = title
        self.name = title.replace(' ', '-').lower()
        self.uri = uri if uri else resource_tmpl.format(self.name)
        self.icon_name = icon if icon else icon_tmpl.format(self.name)


'''
SoundWidget object
Create a widget to show, play and manage a Sound
'''
class SoundWidget(Handy.ActionRow):

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
        icon.set_pixel_size(96)
        self.add_prefix(icon)

    def change_vol(self, scale):
        volume = scale.get_value()
        self.player.set_volume(volume)


'''
SoundPlayer object
Create and controll a GStreamer playbin with the given Sound

Based on Focusli JavaScript code
https://github.com/armonge/gnome-shell-extension-focusli
Copyright (C) 2017 Felipe Borges <felipeborges@gnome.org>

Ported to Python by Rafael Mardojai CM
'''
class SoundPlayer(object):

    def __init__(self, sound):
        self.playbin = Gst.ElementFactory.make('playbin', sound.name)
        self.playbin.set_property('uri', sound.uri)
        sink = Gst.ElementFactory.make('pulsesink', 'sink')
        self.playbin.set_property('audio-sink',sink)

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

