# Copyright 2020-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GObject, Gtk


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/volume-row.ui')
class VolumeRow(Gtk.ListBoxRow):
    __gtype_name__ = 'VolumeRow'

    title = GObject.Property(type=str)
    volume = GObject.Property(type=float)

    def __init__(self):
        super().__init__()
