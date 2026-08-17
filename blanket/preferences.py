# Copyright 2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from typing import TYPE_CHECKING

from gi.repository import Adw, Gio, Gtk, Xdp, XdpGtk4

from blanket.define import RES_PATH
from blanket.settings import Settings

if TYPE_CHECKING:
    from blanket.window import BlanketWindow


@Gtk.Template(resource_path=f"{RES_PATH}/preferences.ui")
class PreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "PreferencesDialog"

    dark_group: Adw.PreferencesGroup = Gtk.Template.Child()
    dark: Adw.SwitchRow = Gtk.Template.Child()
    autostart: Adw.SwitchRow = Gtk.Template.Child()
    start_paused: Adw.SwitchRow = Gtk.Template.Child()
    inhibition: Adw.SwitchRow = Gtk.Template.Child()

    def __init__(self, window: "BlanketWindow", **kwargs):
        super().__init__(**kwargs)

        self.window = window

        # Show dark theme preference if system does not support color schemes
        self.dark_group.props.visible = (
            not Adw.StyleManager.get_default().props.system_supports_color_schemes
        )
        # Dark theme
        Settings.get().bind(
            "dark-mode", self.dark, "active", Gio.SettingsBindFlags.DEFAULT
        )
        self.dark.connect("notify::active", self._toggle_dark)

        # Autostart
        self.autostart_saved = Settings.get().autostart
        self.autostart.props.active = self.autostart_saved
        self.autostart.connect("notify::active", self._toggle_autostart)

        # Start paused
        Settings.get().bind(
            "start-paused", self.start_paused, "active", Gio.SettingsBindFlags.DEFAULT
        )

        # Inhibition
        Settings.get().bind(
            "inhibit-suspension",
            self.inhibition,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )

    def _toggle_dark(self, switch: Adw.SwitchRow, _pspec):
        style_manager = Adw.StyleManager.get_default()
        if switch.props.active:
            style_manager.props.color_scheme = Adw.ColorScheme.FORCE_DARK
        else:
            style_manager.props.color_scheme = Adw.ColorScheme.PREFER_LIGHT

    def _toggle_autostart(self, switch: Adw.SwitchRow, _pspec):
        self._request_autostart(switch.props.active)

    def _request_autostart(self, active: bool):
        def finish(portal: Xdp.Portal, result: Gio.AsyncResult) -> None:
            try:
                active = self.autostart.get_active()
                success = portal.request_background_finish(result)

                if not success and active:
                    error_dialog = Adw.AlertDialog.new(
                        _("Authorization failed"),
                        _(
                            "Make sure Blanket has permission to run in the background in Settings → Applications → Blanket and try again."
                        ),
                    )
                    error_dialog.add_response("ok", _("Ok"))
                    error_dialog.present(self.window)
                    self.autostart.props.active = self.autostart_saved
                else:
                    Settings.get().autostart = active

            except Exception:
                error_toast = Adw.Toast(title=_("The autostart request failed."))
                self.add_toast(error_toast)
                self.autostart.props.active = self.autostart_saved

        flags = Xdp.BackgroundFlags.AUTOSTART if active else Xdp.BackgroundFlags(0)
        parent = XdpGtk4.parent_new_gtk(
            self.window
        )  # Warning: g_variant_unref: assertion 'value != NULL' failed
        parent = None
        portal = Xdp.Portal()
        portal.request_background(
            parent,
            _("Autostart Blanket in background."),
            ["blanket", "--hidden"],
            flags,
            None,
            finish,
        )
