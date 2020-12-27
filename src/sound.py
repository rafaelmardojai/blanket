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

from gi.repository import GObject, Gst, GstPlayer


class MainPlayer(GObject.GObject):
    """
    Virtual app sounds player
    """

    __gsignals__ = {
        'volume-changed': (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        'playing-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    playing = GObject.Property(type=bool, default=True)
    volume = GObject.Property(type=float, default=0)

    def __init__(self):
        super().__init__()


class SoundObject(GObject.Object):
    """
    Describe a sound with it's propeties
    """

    def __init__(self, name, uri=None, title=None, mainplayer=None,
                 settings=None, custom=False, **kwargs):
        super().__init__(**kwargs)

        resource_tmpl = 'resource:/com/rafaelmardojai/Blanket/sounds/{}.ogg'
        icon_tmpl = 'com.rafaelmardojai.Blanket-{}'

        self.name = name
        self.uri = uri if uri else resource_tmpl.format(name)
        self.title = title if title else name
        self.icon_name = icon_tmpl.format(name)
        self.mainplayer = mainplayer
        self.settings = settings
        self.custom = custom

    def get_saved_volume(self):
        return self.settings.get_sound_volume(self.name)


class SoundPlayer(GstPlayer.Player):
    """
    GstPlayer.Player with modifications
    """

    def __init__(self, sound):
        super().__init__()
        self.sound = sound
        # Create a var to save saved volume
        self.saved_volume = 0.0
        # Alwas start with volume in 0
        self.set_volume(0)

        # Set SoundObject.uri as player uri
        self.set_uri(self.sound.uri)
        self.name = self.sound.name

        # Loop setup
        self.prerolled = False
        self.pipeline = self.get_pipeline()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_bus_message)

        # Connect mainplayer volume-changed signal
        self.volume_hdlr = self.sound.mainplayer.connect(
            'notify::volume',
            self._on_main_volume_changed)
        # Connect mainplayer muted signal
        self.playing_hdlr = self.sound.mainplayer.connect(
            'notify::playing',
            self._on_playing_changed)

        # Connect volume-changed signal
        self.connect('volume-changed', self._on_volume_changed)

    def set_virtual_volume(self, volume):
        # Get mainplayer volume
        main_volume = self.sound.mainplayer.get_property('volume')
        # Get last saved sound volume
        self.saved_volume = volume
        # Multiply sound volume with mainplayer volume
        volume = self.saved_volume * main_volume
        # Set final volume to player
        self.set_volume(volume)

    def remove(self):
        # Stop player
        self.stop()
        # Disconnect main player signals
        self.sound.mainplayer.disconnect(self.volume_hdlr)
        self.sound.mainplayer.disconnect(self.playing_hdlr)

    def _on_playing_changed(self, player, playing):
        playing = self.sound.mainplayer.get_property('playing')

        if not self.__vol_zero():
            if playing:
                self.play()
            else:
                self.pause()

    def _on_volume_changed(self, player):
        # Always play if volume > 0
        playing = self.sound.mainplayer.get_property('playing')

        if self.__vol_zero():
            self.pause()
        elif playing:
            self.play()

    def _on_main_volume_changed(self, player, volume):
        if not self.__vol_zero(self.sound.get_saved_volume()):
            # Set volume again when mainplayer volume changes
            self.set_virtual_volume(self.saved_volume)

    def _on_bus_message(self, bus, message):
        if message:
            if message.type is Gst.MessageType.SEGMENT_DONE:
                self.pipeline.seek_simple(
                    Gst.Format.TIME,
                    Gst.SeekFlags.SEGMENT,
                    0
                )

            if message.type is Gst.MessageType.ASYNC_DONE:
                if not self.prerolled:
                    self.pipeline.seek_simple(
                        Gst.Format.TIME,
                        Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT,
                        0
                    )
                    self.prerolled = True

            return True
        
    def __vol_zero(self, volume=None):
        volume = volume if volume else self.get_volume()
        return True if volume == 0 else False

