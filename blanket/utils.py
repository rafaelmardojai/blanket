# Copyright 2026 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GObject


class DummyItemModel(GObject.Object, Gio.ListModel):
    """
    Model that joins a dummy object to another model.

    This is used by Blanket to have an "add sound" button among sounds.
    """

    def __init__(self, model: Gio.ListModel, dummy: GObject.Object, **kwargs):
        super().__init__(**kwargs)

        self._model = model
        self._dummy = dummy

        # Forward items changed signal
        self._model.connect(
            "items-changed", lambda _m, p, r, a: self.items_changed(p, r, a)
        )

    def do_get_item(self, position: int) -> GObject.Object | None:
        if position == self._model.get_n_items():
            return self._dummy  # Return dummy object
        return self._model.get_item(position)

    def do_get_item_type(self) -> type:
        return GObject.Object

    def do_get_n_items(self) -> int:
        return self._model.get_n_items() + 1
