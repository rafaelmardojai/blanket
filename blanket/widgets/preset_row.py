# Copyright 2021-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject, Gtk

from blanket.define import RES_PATH
from blanket.settings import Settings
from blanket.widgets.preset_dialog import PresetDialog


@Gtk.Template(resource_path=f'{RES_PATH}/preset-row.ui')
class PresetRow(Gtk.ListBoxRow):
    __gtype_name__ = 'PresetRow'

    custom: bool = GObject.Property(type=bool, default=False)  # type: ignore
    selected: bool = GObject.Property(type=bool, default=False)  # type: ignore

    name: Gtk.Label = Gtk.Template.Child()  # type: ignore
    rename_btn: Gtk.Button = Gtk.Template.Child()  # type: ignore
    delete_btn: Gtk.Button = Gtk.Template.Child()  # type: ignore

    def __init__(self, preset):
        super().__init__()

        self.preset = preset
        self.custom = self.preset.id != Settings.get().default_preset

        self.rename_btn.connect('clicked', self._on_show_rename)
        self.delete_btn.connect('clicked', self._on_delete_preset)

        preset.bind_property(
            'active', self, 'selected', GObject.BindingFlags.SYNC_CREATE
        )

        preset.bind_property(
            'name', self.name, 'label', GObject.BindingFlags.SYNC_CREATE
        )

        self.connect('notify::selected', self._on_selected_changed)

    def _on_selected_changed(self, _row, _pspec):
        if self.selected:
            self.add_css_class('selected')
        else:
            self.remove_css_class('selected')

    def _on_show_rename(self, _button):
        # Close popover
        popover: Gtk.Popover = self.get_native()  # type: ignore
        if popover is not None:
            popover.popdown()

        # Open edit dialog
        app = Gio.Application.get_default()
        if app:
            window = app.get_active_window()  # type: ignore
            if window:
                dialog = PresetDialog(self.preset)
                dialog.present(window)

    def _on_delete_preset(self, _button):
        app = Gio.Application.get_default()
        if app:
            window = app.get_active_window()  # type: ignore
            if window:
                active = self.preset.id == Settings.get().active_preset
                index = self.preset.remove()

                if index is not None:
                    chooser = window.presets_chooser
                    chooser.model.remove(index)

                    # Select default preset row
                    if active:
                        chooser.selected = chooser.model.get_item(0)
