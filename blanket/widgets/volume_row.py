# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GObject, Gtk

from blanket.define import RES_PATH


@Gtk.Template(resource_path=f'{RES_PATH}/volume-row.ui')
class VolumeRow(Gtk.ListBoxRow):
    __gtype_name__ = 'VolumeRow'

    title: str = GObject.Property(type=str)  # type: ignore
    volume: float = GObject.Property(type=float)  # type: ignore

    def __init__(self):
        super().__init__()
