# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gi.repository import Gio, GObject, GLib, Gtk

from blanket.define import RES_PATH


@Gtk.Template(resource_path=f'{RES_PATH}/sound-context-menu.ui')
class SoundContextMenu(Gtk.PopoverMenu):
    __gtype_name__ = 'SoundContextMenu'

    volume: Gtk.Scale = Gtk.Template.Child()  # type: ignore

    def __init__(self, sound):
        super().__init__()

        self.sound = sound

        if self.sound.custom:
            # Set remove menu item
            custom_section = Gio.Menu()
            remove_item = Gio.MenuItem.new(_('Remove'), None)
            remove_item.set_action_and_target_value(
                'app.remove-sound', GLib.Variant.new_string(self.sound.name)
            )
            custom_section.insert_item(-1, remove_item)

            self.props.menu_model.append_section(None, custom_section)  # type: ignore

    @Gtk.Template.Callback()
    def on_opened(self, _popup):
        self.volume.set_value(self.sound.saved_volume)

        vol_adjustment = self.volume.get_adjustment()
        self.vol_bind = self.sound.bind_property(
            'saved_volume', vol_adjustment, 'value', GObject.BindingFlags.BIDIRECTIONAL
        )

    def do_closed(self):
        self.vol_bind.unbind()
