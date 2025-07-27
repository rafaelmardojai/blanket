# Copyright 2025 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _

from gi.repository import Adw, Gio, Gtk

from blanket.define import RES_PATH
from blanket.settings import Settings
from blanket.sound import Sound


@Gtk.Template(resource_path=f"{RES_PATH}/sound-rename-dialog.ui")
class SoundRenameDialog(Adw.Dialog):
    __gtype_name__ = "SoundRenameDialog"

    headerbar: Adw.HeaderBar = Gtk.Template.Child()  # type: ignore
    title_widget: Adw.WindowTitle = Gtk.Template.Child()  # type: ignore
    accept_btn: Gtk.Button = Gtk.Template.Child()  # type: ignore
    name_entry: Adw.EntryRow = Gtk.Template.Child()  # type: ignore

    def __init__(self, sound: Sound, index: int, **kwargs):
        super().__init__()

        self.sound = sound
        self.index = index
        app = Gio.Application.get_default()
        self.window = app.get_active_window()  # type: ignore

        self.set_title(_("Rename Sound"))
        self.title_widget.set_subtitle(self.sound.name)
        self.name_entry.set_text(self.sound.name)
        # Wire buttons
        self.accept_btn.connect("clicked", self._on_rename_sound)

        self.connect("realize", Gio.Application.get_default().unset_space_accel)  # type: ignore
        self.connect("closed", Gio.Application.get_default().set_space_accel)  # type: ignore

    @Gtk.Template.Callback()
    def _on_cancel_clicked(self, _button):
        self.close()

    @Gtk.Template.Callback()
    def _on_entry_changed(self, _entry):
        name = self.__get_name()

        if self.sound is not None and (
            self.sound.name == name or name in Settings.get().custom_audios
        ):
            self.accept_btn.set_sensitive(False)
            return

        if name:
            self.accept_btn.set_sensitive(True)
        else:
            self.accept_btn.set_sensitive(False)

    def _on_rename_sound(self, _button):
        new_name = self.__get_name()

        if new_name == self.sound.name:
            self.close()
            return

        if not new_name or new_name in Settings.get().custom_audios:
            self.__invalid_name()
            return

        Settings.get().rename_custom_audio(self.sound.name, new_name)
        self.sound.name = new_name
        self.sound.title = new_name

        self.close()

    def __get_name(self):
        name = self.name_entry.get_text()
        name = name.strip()  # Strip name

        return name

    def __invalid_name(self):
        pass
