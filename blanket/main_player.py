# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject, Gtk


class MainPlayer(GObject.GObject, Gio.ListModel):
    """
    Virtual app sounds player

    It also implements Gio.ListModel and stores the app sound list.
    """
    _instance = None
    _cookie = 0
    _sounds = []  # Sound list

    __gtype_name__ = 'MainPlayer'
    __gsignals__ = {
        'preset-changed': (GObject.SIGNAL_RUN_FIRST, None, (GObject.Object,)),
        'reset-volumes': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    playing = GObject.Property(type=bool, default=True)
    volume = GObject.Property(type=float, default=0)

    @classmethod
    def get(cls):
        """Return an active instance of Settings."""
        if cls._instance is None:
            cls._instance = MainPlayer()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.connect('notify::playing', self._on_playing)

    def mute_vol_zero(self):
        for sound in self:
            if sound.saved_volume == 0:
                sound.playing = False

    def change_preset(self, preset):
        self.emit('preset-changed', preset)

    def reset_volumes(self):
        self.emit('reset-volumes')

    def _on_playing(self, _player, _param):
        """
        Toggle suspension inhibition when playing
        """
        app = Gtk.Application.get_default()

        if self.playing:
            self._cookie = app.inhibit(
                None,
                Gtk.ApplicationInhibitFlags.SUSPEND,
                'Playback in progress'
            )
        elif self._cookie != 0:
            app.uninhibit(self._cookie)

    """
    ListModel methods
    """

    def __iter__(self):
        return iter(self._sounds)

    def do_get_item(self, position):
        return self._sounds[position]

    def do_get_item_type(self):
        return GObject.Object

    def do_get_n_items(self):
        return len(self._sounds)

    def append(self, sound):
        self._sounds.append(sound)
        self.items_changed(len(self._sounds) - 1, 0, 1)

    def remove(self, position):
        del self._sounds[position]
        self.items_changed(position, 1, 0)
