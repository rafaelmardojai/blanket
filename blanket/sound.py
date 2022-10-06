# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject, Gtk, Gst
from gi.repository.GstPlay import Play

from blanket.settings import Settings


class MainPlayer(GObject.GObject):
    """
    Virtual app sounds player
    """
    __gtype_name__ = 'MainPlayer'
    __gsignals__ = {
        'preset-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'reset-volumes': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    playing = GObject.Property(type=bool, default=True)
    volume = GObject.Property(type=float, default=0)

    def __init__(self):
        super().__init__()

    def preset_changed(self):
        self.playing = True
        self.emit('preset-changed')

    def reset_volumes(self):
        self.emit('reset-volumes')


class SoundObject(GObject.Object):
    """
    Describe a sound with it's propeties
    """
    __gtype_name__ = 'SoundObject'

    def __init__(self, name, uri=None, title=None, mainplayer=None,
                 custom=False, **kwargs):
        super().__init__(**kwargs)

        resource_tmpl = 'resource:/com/rafaelmardojai/Blanket/sounds/{}.ogg'
        icon_tmpl = 'com.rafaelmardojai.Blanket-{}'

        self.name = name
        self.uri = uri if uri else resource_tmpl.format(name)
        self.title = title if title else name
        self.icon_name = icon_tmpl.format('sound-wave' if custom else name)
        self.mainplayer = mainplayer
        self.custom = custom

    @property
    def saved_volume(self):
        return Settings.get().get_sound_volume(self.name)

    @saved_volume.setter
    def saved_volume(self, volume):
        Settings.get().set_sound_volume(self.name, volume)

    @property
    def saved_mute(self):
        return Settings.get().get_sound_mute(self.name)

    @saved_mute.setter
    def saved_mute(self, mute):
        Settings.get().set_sound_mute(self.name, mute)

    def remove(self):
        if self.custom:
            Settings.get().remove_custom_audio(self.name)


class SoundPlayer(Play):
    """
    GstPlayer.Player with modifications
    """
    __gtype_name__ = 'SoundPlayer'

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

        # Connect mainplayer volume signal
        self.volume_hdlr = self.sound.mainplayer.connect(
            'notify::volume',
            self._on_main_volume_changed)
        # Connect mainplayer muted signal
        self.playing_hdlr = self.sound.mainplayer.connect(
            'notify::playing',
            self._on_playing_changed)

        # Connect volume-changed signal
        self.connect('notify::volume', self._on_volume_changed)

    def set_virtual_volume(self, volume):
        # Get last saved sound volume
        self.saved_volume = volume
        # Multiply sound volume with mainplayer volume
        volume = self.saved_volume * self.sound.mainplayer.volume
        # Set final volume to player
        self.set_volume(volume)

    def remove(self):
        # Stop player
        self.stop()
        # Disconnect main player signals
        self.sound.mainplayer.disconnect(self.volume_hdlr)
        self.sound.mainplayer.disconnect(self.playing_hdlr)

    def _on_playing_changed(self, _player, _volume):
        if not self.__vol_zero():
            if self.sound.mainplayer.playing:
                self.play()
            else:
                self.pause()

    def _on_volume_changed(self, _player, _volume):
        # Fix external changes to player volume
        volume = self.saved_volume * self.sound.mainplayer.volume
        if volume > 0 and self.get_volume() == 0.0:
            self.set_volume(volume)
            return
        # Only play if volume > 0
        if self.__vol_zero():
            self.pause()
        elif self.sound.mainplayer.playing:
            self.play()

    def _on_main_volume_changed(self, _player, _volume):
        if not self.__vol_zero(self.sound.saved_volume):
            # Set volume again when mainplayer volume changes
            self.set_virtual_volume(self.saved_volume)

    def _on_bus_message(self, _bus, message):
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
