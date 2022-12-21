# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstPlay', '1.0')
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


AUTHORS = [
    'Rafael Mardojai CM'
]

ARTISTS = {
    'Jakub Steiner': [_('Sounds icons')],
    'Rafael Mardojai CM': [_('App icon')]
}

SOUND_ARTISTS = {
    'alex36917': [_('Rain')],
    'Digifish music': [_('Storm')],
    'ezwa': [_('Fireplace')],
    'Falcet': [_('Boat')],
    'gezortenplotz': [_('City')],
    'gluckose': [_('Stream')],
    'Jorge Stolfi': [_('White Noise')],
    'kvgarlic': [_('Birds')],
    'Lisa Redfern': [_('Summer Night')],
    'Luftrum': [_('Waves')],
    'stephan': [_('Coffee Shop')],
    'Omegatron': [_('Pink Noise')],
    'felix.blume': [_('Wind')],
    'vahid': [_('Train')],
}

SOUND_EDITORS = {
    'Porrumentzio': [
        _('Birds'), _('Rain'), _('Storm'), _('Waves'), _('Boat'), _('City'), _('Wind')]
}

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

    def do_startup(self):
        # Startup application
        Adw.Application.do_startup(self)

        style_manager = Adw.StyleManager.get_default()
        # if the system doesn't support libadwaita color schemes, fall back to our setting
        if Settings.get().dark_mode and not style_manager.props.system_supports_color_schemes:
            style_manager.props.color_scheme = Adw.ColorScheme.FORCE_DARK

        # Start MPRIS server
        self.mpris = MPRIS(self)

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
                'func': self.on_preferences,
                'accels': ['<Ctl>comma']
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
            self.window = BlanketWindow(self.mpris, application=self)

        self.window.props.hide_on_close = Settings.get().background

        if self.window_hidden:
            self.window.hide()
            self.window_hidden = False
        else:
            self.window.present()

        # Connect window close-request signal to _on_window_close_request
        self.window.connect('close-request', self._on_window_close_request)

        # Load saved props
        MainPlayer.get().volume = Settings.get().volume
        MainPlayer.get().playing = Settings.get().playing

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
        playing = MainPlayer.get().playing
        playing = False if playing else True

        # Change mainplayer playing
        MainPlayer.get().playing = playing

    def on_play(self, _action=None, _param=None):
        MainPlayer.get().playing = True

    def on_pause(self, _action=None, _param=None):
        MainPlayer.get().playing = False

    def on_reset_volumes(self, _action, _param):
        MainPlayer.get().reset_volumes()

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

    def on_about(self, _action, _param):
        builder = Gtk.Builder.new_from_resource('/com/rafaelmardojai/Blanket/about.ui')
        about = builder.get_object('about')

        artists = self.__get_credits_list(ARTISTS)
        sound_artists = self.__get_credits_list(SOUND_ARTISTS)
        sound_editors = self.__get_credits_list(SOUND_EDITORS)

        about.set_version(self.version)
        about.set_developers(AUTHORS)
        about.set_designers(artists)
        about.add_credit_section(_('Sounds by'), sound_artists)
        about.add_credit_section(_('Sounds edited by'), sound_editors)

        about.set_transient_for(self.window)
        about.present()

    def on_close(self, _action, _param):
        self.window.close()

    def on_quit(self, _action, _param):
        self.quit()

    def _save_settings(self):
        # Save mainplayer volume
        Settings.get().volume = MainPlayer.get().volume
        # Save mainplayer playing state
        Settings.get().playing = MainPlayer.get().playing
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

    def __get_credits_list(self, dict_):
        credits_list = []
        for k, vs in dict_.items():
            s = k + ': ' + ', '.join(vs)
            credits_list.append(s)
        return credits_list


def main(version):
    app = Application(version)
    return app.run(sys.argv)
