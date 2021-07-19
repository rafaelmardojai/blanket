# Copyright 2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject, Gtk

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
            Settings.get().remove_preset(self.id)
            return True
        return False


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/preset-chooser.ui')
class PresetChooser(Gtk.Box):
    __gtype_name__ = 'PresetChooser'
    __gsignals__ = {
        'selected': (GObject.SIGNAL_RUN_FIRST, None, (PresetObject,))
    }
    selected = GObject.Property(type=PresetObject)
    index = GObject.Property(type=int)

    presets_list = Gtk.Template.Child()
    add_btn = Gtk.Template.Child()
    add_preset = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    create_btn = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)

        self.window = window

        # Create GioListStore to store Presets
        self.model = Gio.ListStore.new(PresetObject)
        self.presets_list.bind_model(self.model, self._create_widget)

        # Wire widgets
        self.presets_list.connect('row-selected', self._on_preset_selected)
        self.create_btn.connect('clicked', self._on_create_preset)
        self.name_entry.connect('activate', self._on_create_preset)

        self.load_presets()

    def load_presets(self):
        presets = Settings.get().get_presets_dict()
        active = Settings.get().active_preset
        selected = 0
        for index, (preset_id, name) in enumerate(presets.items()):
            preset = PresetObject(preset_id, self.model)
            self.model.append(preset)

            if preset_id == active:
                selected = index

        row = self.presets_list.get_row_at_index(selected)
        self.presets_list.select_row(row)

    def _on_preset_selected(self, _listbox, row):
        index = 0 if row is None else row.get_index()
        preset = self.model.get_item(index)
        if preset is not None:
            if Settings.get().active_preset != preset.id:
                Settings.get().active_preset = preset.id
                self.window.flap.set_reveal_flap(False)

        self.selected = preset
        self.index = index
        self.emit('selected', preset)

    def _create_widget(self, preset):
        widget = PresetRow(preset)
        return widget

    def _on_create_preset(self, _widget):
        # Hide popover
        self.add_preset.popdown()

        name = self.name_entry.get_text()
        name = name.strip()  # Strip nane
        if name:
            preset_id = Settings.get().add_preset(name)  # Save new preset
            preset = PresetObject(preset_id, self.model)  # Add preset to model
            self.model.append(preset)

        # Clear name entry
        self.name_entry.set_text('')


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/preset-control.ui')
class PresetControl(Gtk.Box):
    __gtype_name__ = 'PresetControl'
    __gsignals__ = {
        'reset': (GObject.SIGNAL_RUN_FIRST, None, (PresetObject,))
    }

    toggle_btn = Gtk.Template.Child()
    preset_name = Gtk.Template.Child()

    menu = Gtk.Template.Child()
    volume_btn = Gtk.Template.Child()
    rename_btn = Gtk.Template.Child()
    delete_btn = Gtk.Template.Child()

    rename = Gtk.Template.Child()
    rename_entry = Gtk.Template.Child()
    rename_confirm_btn = Gtk.Template.Child()
    rename_cancel_btn = Gtk.Template.Child()

    delete = Gtk.Template.Child()
    delete_confirm_btn = Gtk.Template.Child()
    delete_cancel_btn = Gtk.Template.Child()

    preset = None
    default_preset = None
    name_binding = None

    def __init__(self, window):
        super().__init__()

        self.chooser = window.presets

        # Wire toggle with window flap
        self.toggle_btn.bind_property(
            'active', window.flap, 'reveal-flap',
            GObject.BindingFlags.BIDIRECTIONAL
        )
        #
        self.chooser.connect('selected', self.__on_preset_changed)

        # Wire buttons
        self.volume_btn.connect('clicked', self._reset_volumes)
        self.rename_btn.connect('clicked', self._show_rename)
        self.delete_btn.connect('clicked', self._show_delete)
        self.rename_cancel_btn.connect('clicked', self._go_back)
        self.rename_confirm_btn.connect('clicked', self._rename)
        self.rename_entry.connect('activate', self._rename)
        self.delete_cancel_btn.connect('clicked', self._go_back)
        self.delete_confirm_btn.connect('clicked', self._delete)

        # Set initial preset
        self.default_preset = Settings.get().default_preset
        self.preset = self.chooser.selected
        self.name_binding = self.preset.bind_property(
            'name', self.preset_name, 'label', GObject.BindingFlags.SYNC_CREATE
        )

        # If it's default preset, don't allow rename or delete
        self._update_sensitives()

    def _reset_volumes(self, _button):
        self.emit('reset', self.preset)

    def _show_rename(self, _button):
        self.rename.popup()
        self.rename_entry.set_text(Settings.get().active_preset_name)

    def _rename(self, widget):
        self._go_back(widget)
        name = self.rename_entry.get_text()
        Settings.get().set_preset_name(self.preset.id, name)

    def _show_delete(self, _button):
        self.delete.popup()

    def _delete(self, button):
        self._go_back(button)

        if self.preset.remove():
            self.chooser.model.remove(self.chooser.index)

        # Select default preset row
        row = self.chooser.presets_list.get_row_at_index(0)
        self.chooser.presets_list.select_row(row)

    def _go_back(self, widget):
        popover = widget.get_ancestor(Gtk.Popover.__gtype__)
        popover.popdown()

    def _update_sensitives(self):
        sensitive = self.preset.id != self.default_preset
        self.rename_btn.set_sensitive(sensitive)
        self.delete_btn.set_sensitive(sensitive)

    def __on_preset_changed(self, _chooser, preset):
        # Remove previous binding
        self.name_binding.unbind()

        # Update preset
        self.preset = preset
        self.name_binding = self.preset.bind_property(
            'name', self.preset_name, 'label', GObject.BindingFlags.SYNC_CREATE
        )

        # If it's default preset, don't allow rename or delete
        self._update_sensitives()


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/preset-row.ui')
class PresetRow(Gtk.ListBoxRow):
    __gtype_name__ = 'PresetRow'

    name = Gtk.Template.Child()

    def __init__(self, preset):
        super().__init__()

        preset.bind_property(
            'name', self.name, 'label', GObject.BindingFlags.SYNC_CREATE
        )
