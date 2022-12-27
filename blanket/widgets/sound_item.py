# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gdk, GObject, Gtk

from blanket.sound import Sound
from blanket.widgets.sound_context_menu import SoundContextMenu


class SoundItem(Gtk.Box):
    __gtype_name__ = 'SoundItem'

    playing = GObject.Property(type=bool, default=False)
    title = GObject.Property(type=str)
    icon_name = GObject.Property(type=str)
    sound = GObject.Property(type=Sound)

    def __init__(self):
        super().__init__()

        self.props.orientation = Gtk.Orientation.VERTICAL
        self.props.spacing = 6
        self.add_css_class('sound-item')

        self.connect('notify::playing', self._playing_changed)

        # Icon
        self.icon = Gtk.Image(pixel_size=64, halign=Gtk.Align.CENTER)
        self.bind_property(
            'icon_name', self.icon, 'icon_name',
            GObject.BindingFlags.SYNC_CREATE
        )
        self.append(self.icon)

        # Label
        self.label = Gtk.Label()
        self.bind_property(
            'title', self.label, 'label', GObject.BindingFlags.SYNC_CREATE
        )
        self.append(self.label)

        click = Gtk.GestureClick()
        click.set_button(3)  # Listen to secondary button (aka right-click)
        click.connect('pressed', self._on_secondary_click)
        self.add_controller(click)

    def _playing_changed(self, _object, _pspec):
        if not self.playing:
            self.icon.remove_css_class('accent')
        elif not self.icon.has_css_class('accent'):
            self.icon.add_css_class('accent')

    def _on_secondary_click(self, _ctrl, _n, x, y):
        self._context_popover(x, y)

    def _context_popover(self, x, y):
        menu = SoundContextMenu(self.sound)

        rec = Gdk.Rectangle()
        rec.x = x
        rec.y = y
        rec.width = 0
        rec.height = 0

        menu.set_parent(self)
        menu.set_pointing_to(rec)
        menu.show()
