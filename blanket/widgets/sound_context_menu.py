# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gi.repository import Gio, GObject, GLib, Gtk

from blanket.define import RES_PATH
from blanket.sound import Sound
from blanket.main_player import MainPlayer

@Gtk.Template(resource_path=f'{RES_PATH}/sound-context-menu.ui')
class SoundContextMenu(Gtk.PopoverMenu):
    __gtype_name__ = 'SoundContextMenu'

    volume: Gtk.Scale = Gtk.Template.Child()  # type: ignore

    def __init__(self, sound: Sound):
        super().__init__()

        self.sound: Sound = sound

        if self.sound.custom:
            index = MainPlayer.get().get_index(sound.name)
            # Set remove menu item
            custom_section = Gio.Menu()
            self.rename_item = Gio.MenuItem.new(_('Rename'), None)
            self.rename_item.set_action_and_target_value(
                'app.rename-sound', GLib.Variant.new_uint32(index)
            )
            custom_section.append_item(self.rename_item)
            self.remove_item = Gio.MenuItem.new(_('Remove'), None)
            self.remove_item.set_action_and_target_value(
                'app.remove-sound', GLib.Variant.new_uint32(index)
            )
            custom_section.append_item(self.remove_item)

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
