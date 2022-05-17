# Copyright 2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gi.repository import Gio, GObject, Gtk, Adw

from blanket.settings import Settings


class PresetObject(GObject.Object):
    __gtype_name__ = 'PresetObject'

    name = GObject.Property(type=str)

    def __init__(self, preset_id, model):
        super().__init__()

        self.id = preset_id
        self.model = model

        # Bind preset name with settings one
        Settings.get().get_preset_settings(self.id).bind(
            'visible-name', self, 'name', Gio.SettingsBindFlags.DEFAULT
        )

    def remove(self):
        if self.id != Settings.get().default_preset:
            index = Settings.get().remove_preset(self.id)
            return index  # Return the index where the preset where positioned
        return None


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/preset-chooser.ui')
class PresetChooser(Gtk.Box):
    __gtype_name__ = 'PresetChooser'
    __gsignals__ = {
        'selected': (GObject.SIGNAL_RUN_FIRST, None, (PresetObject,))
    }
    selected = GObject.Property(type=PresetObject)

    presets_list = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        # Create GioListStore to store Presets
        self.model = Gio.ListStore.new(PresetObject)
        self.presets_list.bind_model(self.model, self._create_widget)
        self.connect('notify::selected', self._on_selected_changed)

        # Wire widgets
        self.presets_list.connect('row-activated', self._on_preset_activated)

        self.load_presets()

    def load_presets(self):
        presets = Settings.get().get_presets_dict()
        for index, (preset_id, name) in enumerate(presets.items()):
            preset = PresetObject(preset_id, self.model)
            self.model.append(preset)

            if preset_id == Settings.get().active_preset:
                self.selected = preset

    def _on_preset_activated(self, _listbox, row):
        index = 0 if row is None else row.get_index()
        preset = self.model.get_item(index)

        self.selected = preset

    def _on_selected_changed(self, _chooser, _pspec):
        if self.selected is not None:
            if Settings.get().active_preset != self.selected.id:
                Settings.get().active_preset = self.selected.id

        for i in range(self.model.get_n_items()):
            row = self.presets_list.get_row_at_index(i)
            row.selected = row.preset.id == self.selected.id

        self.emit('selected', self.selected)

    def _create_widget(self, preset):
        widget = PresetRow(preset)
        if preset.id == Settings.get().active_preset:
            widget.selected = True
        return widget


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
        self.cancel_btn.connect(
            'clicked',
            lambda _button: self.destroy()
        )
        self.name_entry.connect('changed', self._on_entry_changed)

        if self.preset is None:
            self.set_title(_('Add Preset'))
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
            preset = PresetObject(preset_id, chooser.model)
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


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/preset-row.ui')
class PresetRow(Gtk.ListBoxRow):
    __gtype_name__ = 'PresetRow'

    name = Gtk.Template.Child()
    indicator = Gtk.Template.Child()
    rename_btn = Gtk.Template.Child()
    delete_btn = Gtk.Template.Child()
    revealer = Gtk.Template.Child()

    def __init__(self, preset):
        super().__init__()

        self.preset = preset

        self.rename_btn.connect('clicked', self._on_show_rename)
        self.delete_btn.connect('clicked', self._on_delete_preset)
        self.revealer.props.reveal_child = self.preset.id != Settings.get().default_preset

        preset.bind_property(
            'name', self.name, 'label', GObject.BindingFlags.SYNC_CREATE
        )

    @property
    def selected(self):
        return self.indicator.get_visible()

    @selected.setter
    def selected(self, value):
        self.indicator.set_visible(value)
        if value:
            self.add_css_class('selected')
        else:
            self.remove_css_class('selected')

    def _on_show_rename(self, _button):
        app = Gio.Application.get_default()
        window = app.get_active_window()
        dialog = PresetDialog(self.preset)
        dialog.set_transient_for(window)
        dialog.set_modal(True)
        dialog.present()

    def _on_delete_preset(self, _button):
        app = Gio.Application.get_default()
        window = app.get_active_window()
        active = self.preset.id == Settings.get().active_preset
        index = self.preset.remove()

        if index is not None:
            chooser = window.presets_chooser
            chooser.model.remove(index)

            # Select default preset row
            if active:
                chooser.selected = chooser.model.get_item(0)
