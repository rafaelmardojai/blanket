# Copyright 2021-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject

from blanket.settings import Settings


class Preset(GObject.Object):
    __gtype_name__ = 'Preset'

    name: str = GObject.Property(type=str)  # type: ignore
    active: bool = GObject.Property(type=bool, default=False)  # type: ignore

    def __init__(self, preset_id: str):
        super().__init__()

        self.id = preset_id

        # Active state
        self.active = Settings.get().active_preset == self.id
        Settings.get().connect('changed::active-preset', self._on_active_preset_changed)

        # Bind preset name with settings one
        Settings.get().get_preset_settings(self.id).bind(
            'visible-name', self, 'name', Gio.SettingsBindFlags.DEFAULT
        )

    def remove(self) -> int | None:
        if self.id != Settings.get().default_preset:
            index = Settings.get().remove_preset(self.id)
            return index  # Return the index where the preset where positioned
        return None

    def _on_active_preset_changed(self, _settings, _key):
        self.active = Settings.get().active_preset == self.id
