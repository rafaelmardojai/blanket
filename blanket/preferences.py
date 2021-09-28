# Copyright 2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from random import randint

from gettext import gettext as _
from gi.repository import Gio, GLib, Gtk, Adw

from blanket.settings import Settings


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'

    dark = Gtk.Template.Child()
    autostart = Gtk.Template.Child()

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)

        self.window = window

        Settings.get().bind(
            'dark-mode', self.dark, 'active', Gio.SettingsBindFlags.DEFAULT
        )
        self.dark.connect('notify::active', self._toggle_dark)

        self.autostart_failed = False
        self.autostart_saved = Settings.get().autostart
        self.autostart.set_active(self.autostart_saved)
        self.autostart.connect('notify::active', self._toggle_autostart)

    def _toggle_dark(self, switch, _active):
        gtk_settings = Gtk.Settings.get_default()
        active = switch.get_active()
        gtk_settings.set_property('gtk-application-prefer-dark-theme', active)

    def _toggle_autostart(self, switch, _active):
        active = switch.get_active()
        self.__request_autostart(active)

    def __request_autostart(self, active):
        if self.autostart_failed:
            self.autostart_failed = False
            return

        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(bus, Gio.DBusProxyFlags.NONE, None,
                                       'org.freedesktop.portal.Desktop',
                                       '/org/freedesktop/portal/desktop',
                                       'org.freedesktop.portal.Background',
                                       None)

        identifier = self.__get_window_identifier()
        token = 0 + randint(10000000, 90000000)
        options = {
            'handle_token': GLib.Variant(
                's', f'com/rafaelmardojai/Blanket/{token}'
            ),
            'reason': GLib.Variant('s', _('Autostart Blanket in background.')),
            'autostart': GLib.Variant('b', active),
            'commandline': GLib.Variant('as', ['blanket', '--hidden']),
            'dbus-activatable': GLib.Variant('b', False)
        }

        try:
            request = proxy.RequestBackground('(sa{sv})', identifier, options)
            if request is None:
                raise Exception("The DBus proxy didn't return an object path."
                                + "\nThe portal can't suscribe to the signal.")

            bus.signal_subscribe(
                'org.freedesktop.portal.Desktop',
                'org.freedesktop.portal.Request',
                'Response',
                request,
                None,
                Gio.DBusSignalFlags.NO_MATCH_RULE,
                self.__receive_autostart,
                None
            )

        except Exception as e:
            print(e)

            error_dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK, text=_('Request error')
            )
            error_dialog.props.transient_for = self
            error_dialog.props.modal = True
            error_dialog.props.secondary_text =_('The autostart request failed.')
            error_dialog.connect('response', self.__on_dialog_response)
            error_dialog.present()
            self.autostart_failed = True
            self.autostart.set_active(self.autostart_saved)

    def __receive_autostart(self, *args):
        self.window.present()

        active = self.autostart.get_active()
        state = args[5][0]
        autostart = args[5][1]['autostart']

        if state == 0:
            pass
        elif state == 1:
            if active:
                error_dialog = Gtk.MessageDialog(
                    message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
                    text=_('Authorization failed')
                )
                error_dialog.props.transient_for = self
                error_dialog.props.modal = True
                error_dialog.props.secondary_text = _('Make sure Blanket has permission to run in '
                                                    '\nthe background in Settings → Applications → '
                                                    '\nBlanket and try again.')
                error_dialog.connect('response', self.__on_dialog_response)
                error_dialog.present()
        elif state == 2:
            error_dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
                text=_('Request error')
            )
            error_dialog.props.transient_for = self
            error_dialog.props.modal = True
            error_dialog.props.secondary_text = _('The autostart request failed.')
            error_dialog.connect('response', self.__on_dialog_response)
            error_dialog.present()

        self.autostart.set_active(autostart)
        Settings.get().autostart = autostart
        return

    def __on_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            dialog.destroy()

    def __get_window_identifier(self):
        session = os.getenv('XDG_SESSION_TYPE')
        surface = self.window.get_surface()

        if session == 'x11':
            return f'x11:{str(surface.get_xid())}'
        elif session == 'wayland':
            return 'wayland:'
        return ''
