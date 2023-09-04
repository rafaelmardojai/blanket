# Copyright 2021-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gi.repository import Gio, Gtk, Adw

from blanket.define import RES_PATH
from blanket.preset import Preset
from blanket.settings import Settings


@Gtk.Template(resource_path=f'{RES_PATH}/preset-dialog.ui')
class PresetDialog(Adw.Window):
    __gtype_name__ = 'PresetDialog'

    headerbar: Adw.HeaderBar = Gtk.Template.Child()  # type: ignore
    title_widget: Adw.WindowTitle = Gtk.Template.Child()  # type: ignore
    accept_btn: Gtk.Button = Gtk.Template.Child()  # type: ignore
    name_entry: Adw.EntryRow = Gtk.Template.Child()  # type: ignore

    def __init__(self, preset=None, **kwargs):
        super().__init__()

        self.preset = preset
        app = Gio.Application.get_default()
        self.window = app.get_active_window()  # type: ignore

        if self.preset is None:
            self.set_title(_('New Preset'))
            # Wire buttons
            self.accept_btn.connect('clicked', self._on_create_preset)
        else:
            self.set_title(_('Edit Preset'))
            self.title_widget.set_subtitle(self.preset.name)
            self.name_entry.set_text(self.preset.name)
            # Wire buttons
            self.accept_btn.connect('clicked', self._on_rename_preset)

    @Gtk.Template.Callback()
    def _on_cancel_clicked(self, _button):
        self.close()

    @Gtk.Template.Callback()
    def _on_entry_changed(self, _entry):
        name = self.__get_name()

        if self.preset is not None and self.preset.name == name:
            self.accept_btn.set_sensitive(False)
            return

        if name:
            self.accept_btn.set_sensitive(True)
        else:
            self.accept_btn.set_sensitive(False)

    def _on_create_preset(self, _button):
        name = self.__get_name()
        if name:
            chooser = self.window.presets_chooser
            preset_id = Settings.get().add_preset(name)  # Save new preset
            # Add preset to model
            preset = Preset(preset_id)
            chooser.model.append(preset)

            # Select new preset
            chooser.selected = preset
        else:
            self.__invalid_name()
            return

        # Clear name entry
        self.name_entry.set_text('')

        self.destroy()

    def _on_rename_preset(self, _button):
        if self.preset:
            name = self.__get_name()
            if name:
                Settings.get().set_preset_name(self.preset.id, name)
            else:
                self.__invalid_name()
                return

        self.destroy()

    def __get_name(self):
        name = self.name_entry.get_text()
        name = name.strip()  # Strip name

        return name

    def __invalid_name(self):
        pass
