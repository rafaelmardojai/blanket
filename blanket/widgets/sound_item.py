# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gdk, GObject, Gtk

from blanket.define import RES_PATH
from blanket.sound import Sound
from blanket.widgets.sound_context_menu import SoundContextMenu


@Gtk.Template(resource_path=f'{RES_PATH}/sound-item.ui')
class SoundItem(Gtk.FlowBoxChild):
    __gtype_name__ = 'SoundItem'

    playing: bool = GObject.Property(type=bool, default=False)  # type: ignore
    title: str = GObject.Property(type=str)  # type: ignore
    icon_name: str = GObject.Property(type=str)  # type: ignore
    sound: Sound = GObject.Property(type=Sound)  # type: ignore

    icon: Gtk.Image = Gtk.Template.Child()  # type: ignore
    label: Gtk.Label = Gtk.Template.Child()  # type: ignore
    volume: Gtk.Scale = Gtk.Template.Child()  # type: ignore

    def __init__(self):
        super().__init__()

        self._sound: Sound | None = None
        self._menu: None | SoundContextMenu = None

        self.connect('notify::playing', self._playing_changed)

        # Icon
        self.bind_property(
            'icon_name', self.icon, 'icon_name', GObject.BindingFlags.SYNC_CREATE
        )
        # Label
        self.bind_property(
            'title', self.label, 'label', GObject.BindingFlags.SYNC_CREATE
        )

        click = Gtk.GestureClick()
        click.set_button(3)  # Listen to secondary button (aka right-click)
        click.connect('pressed', self._on_secondary_click)
        self.add_controller(click)

    @GObject.Property(type=Sound)
    def sound(self) -> Sound | None:  # type: ignore
        return self._sound

    @sound.setter
    def sound(self, value: Sound):
        self._sound = value

        if self._sound is not None:
            vol_adjustment = self.volume.get_adjustment()

            vol_adjustment.props.value = self._sound.saved_volume
            self.volume.props.sensitive = self._sound.playing

            self._sound.bind_property(
                'saved_volume',
                vol_adjustment,
                'value',
                GObject.BindingFlags.BIDIRECTIONAL,
            )
            self._sound.bind_property(
                'playing', self.volume, 'sensitive', GObject.BindingFlags.DEFAULT
            )

            self.volume.props.visible = True

    def _playing_changed(self, _object, _pspec):
        if not self.playing:
            self.icon.remove_css_class('accent')
        elif not self.icon.has_css_class('accent'):
            self.icon.add_css_class('accent')

    def _on_secondary_click(self, _ctrl, _n, x: int, y: int):
        self._context_popover(x, y)

    def _context_popover(self, x: int, y: int):
        if self.sound is not None:
            if self._menu is None:
                self._menu = SoundContextMenu(self.sound)

                rec = Gdk.Rectangle()
                rec.x = x
                rec.y = y

                self._menu.set_parent(self)
                self._menu.set_pointing_to(rec)

            self._menu.popup()
