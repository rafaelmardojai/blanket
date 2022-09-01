# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstPlayer', '1.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gettext import gettext as _
from gi.repository import GLib, Gst, Gdk, Gio, Gtk, Adw
# Init GStreamer
Gst.init(None)

from blanket.mpris import MPRIS
from blanket.sound import MainPlayer
from blanket.settings import Settings
from blanket.window import BlanketWindow
from blanket.preferences import PreferencesWindow
from blanket.presets import PresetDialog
from blanket.about import AboutDialog


class Application(Adw.Application):
    def __init__(self, version):
        super().__init__(application_id='com.rafaelmardojai.Blanket',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        GLib.set_application_name(_('Blanket'))
        GLib.setenv('PULSE_PROP_application.icon_name',
                    'com.rafaelmardojai.Blanket-symbolic', True)
        # Connect app shutdown signal
        self.connect('shutdown', self._on_shutdown)

        # Add --hidden command line option
        self.add_main_option('hidden', b'h', GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, 'Start window hidden', None)
        # App window
        self.window = None
        self.window_hidden = False
        # App version
        self.version = version
        # App main player
        self.mainplayer = MainPlayer()
        # Load saved props
        self.mainplayer.volume = Settings.get().volume
        self.mainplayer.playing = Settings.get().playing

        # Start MPRIS server
        self.mpris = MPRIS(self)

    def do_startup(self):
        # Startup application
        Adw.Application.do_startup(self)

        style_manager = Adw.StyleManager.get_default()
        # if the system doesn't support libadwaita color schemes, fall back to our setting
        if Settings.get().dark_mode and not style_manager.props.system_supports_color_schemes:
            style_manager.props.color_scheme = Adw.ColorScheme.FORCE_DARK

        self.setup_actions()

    def setup_actions(self):
        actions = [
            {
                'name': 'open',
                'func': self.on_open,
                'accels': ['<Ctl>o']
            },
            {
                'name': 'playpause',
                'func': self.on_playpause,
                'accels': ['<Ctl>m', 'space']
            },
            {
                'name': 'reset-volumes',
                'func': self.on_reset_volumes,
            },
            {
                'name': 'add-preset',
                'func': self.on_add_preset,
            },
            {
                'name': 'background-playback',
                'func': self.on_background,
                'state': True
            },
            {
                'name': 'preferences',
                'func': self.on_preferences
            },
            {
                'name': 'shortcuts',
                'func': self.on_shortcuts
            },
            {
                'name': 'about',
                'func': self.on_about
            },
            {
                'name': 'close',
                'func': self.on_close,
                'accels': ['<Ctl>w']
            },
            {
                'name': 'quit',
                'func': self.on_quit,
                'accels': ['<Ctl>q']
            }
        ]

        for a in actions:
            if 'state' in a:
                action = Gio.SimpleAction.new_stateful(
                    a['name'], None, Settings.get().get_value(a['name']))
                action.connect('change-state', a['func'])
            else:
                action = Gio.SimpleAction.new(a['name'], None)
                action.connect('activate', a['func'])

            self.add_action(action)

            if 'accels' in a:
                self.set_accels_for_action('app.' + a['name'], a['accels'])

    def do_activate(self):
        self.window = self.props.active_window
        if not self.window:
            self.window = BlanketWindow(self.mainplayer, self.mpris, application=self)

        self.window.props.hide_on_close = Settings.get().background

        if self.window_hidden:
            self.window.hide()
            self.window_hidden = False
        else:
            self.window.present()

        # Connect window close-request signal to _on_window_close_request
        self.window.connect('close-request', self._on_window_close_request)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()

        if 'hidden' in options and self.window is None:
            self.window_hidden = True

        self.activate()
        return 0

    def on_open(self, _action, _param):
        self.window.open_audio()

    def on_playpause(self, _action=None, _param=None):
        # Reverse self.playing bool value
        playing = self.mainplayer.playing
        playing = False if playing else True

        # Change mainplayer playing
        self.mainplayer.playing = playing

    def on_reset_volumes(self, _action, _param):
        self.mainplayer.reset_volumes()

    def on_add_preset(self, _action, _param):
        dialog = PresetDialog()
        dialog.set_transient_for(self.window)
        dialog.set_modal(True)
        dialog.present()

    def on_background(self, action, value):
        action.set_state(value)
        Settings.get().background = value
        self.window.props.hide_on_close = value

    def on_preferences(self, _action, _param):
        window = PreferencesWindow(self.window)
        window.set_transient_for(self.window)
        window.set_modal(True)
        window.present()

    def on_shortcuts(self, _action, _param):
        window = Gtk.Builder.new_from_resource(
            '/com/rafaelmardojai/Blanket/shortcuts.ui'
        ).get_object('shortcuts')
        window.set_transient_for(self.window)
        window.props.section_name = 'shortcuts'
        window.set_modal(True)
        window.present()

    def on_about(self, _action, _param):
        dialog = AboutDialog(self.version)
        dialog.set_transient_for(self.window)
        dialog.set_modal(True)
        dialog.present()

    def on_close(self, _action, _param):
        self.window.close()

    def on_quit(self, _action, _param):
        self.quit()

    def _save_settings(self):
        # Save scroll position
        Settings.get().scroll_position = self.window.vscroll.get_value()
        # Save mainplayer volume
        Settings.get().volume = self.mainplayer.volume
        # Save mainplayer playing state
        Settings.get().playing = self.mainplayer.playing
        # Save presets settings
        Settings.get().save_presets()

    def _on_window_close_request(self, window):
        if Settings.get().background:
            self._save_settings()  # Save settings
            window.hide()
        else:
            self.quit_from_window = True
            self.quit()

    def _on_shutdown(self, _app):
        self._save_settings()


def main(version):
    app = Application(version)
    return app.run(sys.argv)
