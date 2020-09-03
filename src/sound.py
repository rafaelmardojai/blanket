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

from gi.repository import GObject, GstPlayer


class MainPlayer(GObject.GObject):
    '''
    Virtual app sounds player
    '''

    __gsignals__ = {
        'volume-changed': (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        'muted': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self):
        super().__init__()

        self.volume = 1

    def set_muted(self, muted):
        self.emit('muted', muted)

    def set_volume(self, volume):
        self.volume = volume
        self.emit('volume-changed', volume)


class SoundObject(GObject.Object):
    '''
    Describe a sound with it's propeties
    '''

    def __init__(self, name, uri=None, title=None, icon=None, removable=False, mainplayer=None, **kwargs):
        super().__init__(**kwargs)

        resource_tmpl = 'resource:////com/rafaelmardojai/Blanket/sounds/{}.ogg'
        icon_tmpl = 'com.rafaelmardojai.Blanket-{}'

        self.name = name
        self.uri = uri if uri else resource_tmpl.format(self.name)
        self.title = title if title else name
        self.icon_name = icon if icon else icon_tmpl.format(self.name)
        self.removable = removable
        self.mainplayer = mainplayer


class SoundPlayer(GstPlayer.Player):
    '''
    GstPlayer.Player with modifications
    '''

    def __init__(self, sound):
        super().__init__()
        # Alwas start with volume in 0
        self.set_volume(0)

        # Set SoundObject.uri as player uri
        self.set_uri(sound.uri)
        self.name = sound.name

        # Connect mainplayer muted signal
        sound.mainplayer.connect('muted', self._on_mute)

        # Connect volume-changed signal
        self.connect('volume-changed', self._on_volume_changed)
        # Connect end-of-stream signal
        self.connect('end-of-stream', self._on_eos)

    def remove(self):
        # Stop player
        self.stop()
        # Unref player
        self.unref()

    def _on_mute(self, player, mute):
        self.set_mute(mute)


    def _on_volume_changed(self, player):
        # Always play if volume > 0
        volume = self.get_volume()
        if volume == 0:
            self.pause()
        else:
            self.play()

    def _on_eos(self, player):
        # Seek player to 0
        self.seek(0)

