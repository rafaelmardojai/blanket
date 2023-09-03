# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GObject, Gtk


class PlayPauseButton(Gtk.Button):
    __gtype_name__ = 'PlayPauseButton'

    playing: bool = GObject.Property(type=bool, default=True)  # type: ignore

    def __init__(self):
        super().__init__()

        self.add_css_class('playpause')
        self.add_css_class('circular')
        self.add_css_class('suggested-action')

        self.connect('notify::playing', self._on_playing_changed)

    def _on_playing_changed(self, _object, _pspec):
        if self.playing:
            self.set_icon_name('media-playback-pause-symbolic')
        else:
            self.set_icon_name('media-playback-start-symbolic')
