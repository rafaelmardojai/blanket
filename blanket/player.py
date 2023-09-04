# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gst, GstPlay

from blanket.main_player import MainPlayer


class Player(GstPlay.Play):
    """
    GstPlay.Play with modifications
    """

    __gtype_name__ = 'SoundPlayer'

    def __init__(self, sound):
        super().__init__()

        self.sound = sound
        # Create a var to save saved volume
        self.saved_volume = 0.0
        # Always start with volume in 0
        self.set_volume(0)

        # Set Sound.uri as player uri
        self.set_uri(self.sound.uri)
        self.name = self.sound.name

        # Loop setup
        self.prerolled = False
        self.pipeline = self.get_pipeline()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_bus_message)

        # Connect mainplayer volume signal
        self.volume_hdlr = MainPlayer.get().connect(
            'notify::volume', self._on_main_volume_changed
        )
        # Connect mainplayer muted signal
        self.playing_hdlr = MainPlayer.get().connect(
            'notify::playing', self._on_playing_changed
        )

        # Connect volume-changed signal
        self.connect('notify::volume', self._on_volume_changed)

    def set_virtual_volume(self, volume: float):
        # Get last saved sound volume
        self.saved_volume = volume
        # Multiply sound volume with mainplayer volume
        volume = self.saved_volume * MainPlayer.get().volume
        # Set final volume to player
        self.set_volume(volume)

    def remove(self):
        # Stop player
        self.stop()
        # Disconnect main player signals
        MainPlayer.get().disconnect(self.volume_hdlr)
        MainPlayer.get().disconnect(self.playing_hdlr)

    def _on_playing_changed(self, _player, _volume):
        if not self.__vol_zero():
            if MainPlayer.get().playing:
                self.play()
            else:
                self.pause()

    def _on_volume_changed(self, _player, _volume):
        # Fix external changes to player volume
        volume = self.saved_volume * MainPlayer.get().volume
        if volume > 0 and self.get_volume() == 0.0:
            self.set_volume(volume)
            return
        # Only play if volume > 0
        if self.__vol_zero():
            self.pause()
        elif MainPlayer.get().playing:
            self.play()

    def _on_main_volume_changed(self, _player, _volume):
        if not self.__vol_zero(self.sound.saved_volume):
            # Set volume again when mainplayer volume changes
            self.set_virtual_volume(self.saved_volume)

    def _on_bus_message(self, _bus, message: Gst.Message):
        if message:
            if message.type is Gst.MessageType.SEGMENT_DONE:
                self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.SEGMENT, 0)

            if message.type is Gst.MessageType.ASYNC_DONE:
                if not self.prerolled:
                    self.pipeline.seek_simple(
                        Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT, 0
                    )
                    self.prerolled = True

            return True

    def __vol_zero(self, volume: float | None = None):
        volume = volume if volume else self.get_volume()
        return True if volume == 0 else False
