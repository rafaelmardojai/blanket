# Copyright 2021-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject

from blanket.settings import Settings


class Preset(GObject.Object):
    __gtype_name__ = 'Preset'

    name = GObject.Property(type=str)
    active = GObject.Property(type=bool, default=False)

    def __init__(self, preset_id):
        super().__init__()

        self.id = preset_id

        self.active = Settings.get().active_preset == self.id
        Settings.get().connect(
            'changed::active-preset', self._on_active_preset_changed
        )

        # Bind preset name with settings one
        Settings.get().get_preset_settings(self.id).bind(
            'visible-name', self, 'name', Gio.SettingsBindFlags.DEFAULT
        )

    def remove(self):
        if self.id != Settings.get().default_preset:
            index = Settings.get().remove_preset(self.id)
            return index  # Return the index where the preset where positioned
        return None

    def _on_active_preset_changed(self, _settings, _key):
        self.active = Settings.get().active_preset == self.id
