# Copyright 2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from random import randint

from gettext import gettext as _
from gi.repository import Gio, GLib, Gtk, Handy


@Gtk.Template(resource_path='/com/rafaelmardojai/Blanket/preferences.ui')
class PreferencesWindow(Handy.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'

    autostart = Gtk.Template.Child()

    def __init__(self, window, settings, **kwargs):
        super().__init__(**kwargs)

        self.window = window
        self.settings = settings

        self.autostart_failed = False
        self.autostart_saved = self.settings.get_boolean('autostart')
        self.autostart.set_active(self.autostart_saved)
        self.autostart.connect('notify::active', self._toggle_autostart)

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
            'handle_token': GLib.Variant('s', f'com/rafaelmardojai/Blanket/{token}'),
            'reason': GLib.Variant('s', _('Autostart Blanket on background.')),
            'autostart': GLib.Variant('b', active),
            'commandline': GLib.Variant('as', ['blanket', '--hidden']),
            'dbus-activatable': GLib.Variant('b', False)
        }

        try:
            request = proxy.RequestBackground('(sa{sv})', identifier, options)
            if request is None:
                raise Exception("The DBus proxy didn't return an object path." \
                                + "\nThe portal can't suscribe to the signal.")

            response_id = bus.signal_subscribe(
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

            error_dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
                                             Gtk.ButtonsType.OK, _('Request error'))
            error_dialog.format_secondary_text(_('The autostart request failed.'))
            error_response = error_dialog.run()
            if error_response == Gtk.ResponseType.OK:
                error_dialog.destroy()

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
                error_dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
                                                 Gtk.ButtonsType.OK, _('Authorization failed'))
                error_dialog.format_secondary_text(
                    _('Make sure Blanket has permission to run in ' \
                      '\nthe background in Settings → Applications → ' \
                      '\nBlanket and try again.'))
                error_response = error_dialog.run()
                if error_response == Gtk.ResponseType.OK:
                    error_dialog.destroy()
        elif state == 2:
            error_dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
                                             Gtk.ButtonsType.OK, _('Request error'))
            error_dialog.format_secondary_text(_('The autostart request failed.'))
            error_response = error_dialog.run()
            if error_response == Gtk.ResponseType.OK:
                error_dialog.destroy()

        self.autostart.set_active(autostart)
        self.settings.set_boolean('autostart', autostart)
        return

    def __get_window_identifier(self):
        session = os.getenv('XDG_SESSION_TYPE')
        window = self.window.get_window()

        if session == 'x11':
            return f'x11:{str(window.get_xid())}'
        elif session == 'wayland':
            return 'wayland:'
        return ''

