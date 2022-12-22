# Copyright 2021-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gi.repository import Gio, Gtk, Adw

from blanket.preset import Preset
from blanket.settings import Settings


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/preset-dialog.ui')
class PresetDialog(Adw.Window):
    __gtype_name__ = 'PresetDialog'

    headerbar = Gtk.Template.Child()
    title_widget = Gtk.Template.Child()
    accept_btn = Gtk.Template.Child()
    cancel_btn = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()

    def __init__(self, preset=None, **kwargs):
        super().__init__()

        self.preset = preset
        app = Gio.Application.get_default()
        self.window = app.get_active_window()

        # Wire widgets
        self.cancel_btn.connect('clicked', lambda _button: self.destroy())
        self.name_entry.connect('changed', self._on_entry_changed)

        if self.preset is None:
            self.set_title(_('New Preset'))
            self.accept_btn.set_label(_('Create'))
            # Wire buttons
            self.accept_btn.connect('clicked', self._on_create_preset)
        else:
            self.set_title(_('Edit Preset'))
            self.title_widget.set_subtitle(self.preset.name)
            self.accept_btn.set_label(_('Save'))
            self.name_entry.set_text(self.preset.name)
            # Wire buttons
            self.accept_btn.connect('clicked', self._on_rename_preset)

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
            preset = Preset(preset_id, chooser.model)
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
