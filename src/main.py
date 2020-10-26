# main.py
#
# Copyright 2020 Rafael Mardojai CM
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstPlayer', '1.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Handy', '1')

from gettext import gettext as _
from gi.repository import GLib, Gst, Gdk, Gio, Gtk, Handy
# Init GStreamer
Gst.init(None)

from .mpris import MPRIS
from .sound import MainPlayer
from .window import BlanketWindow
from .about import AboutDialog


class Application(Gtk.Application):
    def __init__(self, version):
        super().__init__(application_id='com.rafaelmardojai.Blanket',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        GLib.set_application_name(_('Blanket'))
        GLib.set_prgname('com.rafaelmardojai.Blanket')
        GLib.setenv('PULSE_PROP_application.icon_name',
                    'com.rafaelmardojai.Blanket-symbolic', True)

        # Add --hidden command line option
        self.add_main_option('hidden', b'h', GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, 'Start window hidden', None)
        # App window
        self.window = None
        self.window_hidden = False
        # App version
        self.version = version

        # GSettings
        self.gsettings = Gio.Settings.new('com.rafaelmardojai.Blanket')
        # Playing state
        self.playing = self.gsettings.get_boolean('playing')

        # App main player
        self.mainplayer = MainPlayer()
        # Bind mainplayer with settings
        self.gsettings.bind('volume',
                            self.mainplayer, 'volume',
                            Gio.SettingsBindFlags.DEFAULT)
        self.gsettings.bind('playing',
                            self.mainplayer, 'playing',
                            Gio.SettingsBindFlags.DEFAULT)

        # Start MPRIS server
        MPRIS(self)

    def do_startup(self):
        # Startup application
        Gtk.Application.do_startup(self)
        self.setup_actions()
        self.load_css()

        # Init Handy
        Handy.init()

    def setup_actions(self):
        actions = [
            {
                'name'  : 'open',
                'func'  : self.on_open,
                'accels': ['<Ctl>o']
            },
            {
                'name'  : 'playpause',
                'func'  : self.on_playpause,
                'accels': ['<Ctl>m']
            },
            {
                'name'  : 'background-playback',
                'func'  : self.on_background,
                'state' : True
            },
            {
                'name'  : 'shortcuts',
                'func'  : self.on_shortcuts
            },
            {
                'name'  : 'about',
                'func'  : self.on_about
            },
            {
                'name'  : 'close',
                'func'  : self.on_close,
                'accels': ['<Ctl>w']
            },
            {
                'name'  : 'quit',
                'func'  : self.on_quit,
                'accels': ['<Ctl>q']
            }
        ]

        for a in actions:
            if 'state' in a:
                action = Gio.SimpleAction.new_stateful(
                    a['name'], None, self.gsettings.get_value(a['name']))
                action.connect('change-state', a['func'])
            else:
                action = Gio.SimpleAction.new(a['name'], None)
                action.connect('activate', a['func'])

            self.add_action(action)

            if 'accels' in a:
                self.set_accels_for_action('app.' + a['name'], a['accels'])

    def load_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource('/com/rafaelmardojai/Blanket/style.css')
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def do_activate(self):
        self.window = self.props.active_window
        if not self.window:
            self.window = BlanketWindow(self.mainplayer, application=self)

        if self.window_hidden:
            self.window.hide()
            self.window_hidden = False
        else:
            self.window.present()

        # Update window elements to saved playing state
        self.window.update_playing_ui(self.playing)
        # Connect window delete-event signal to _do_close
        self.window.connect('delete-event', self._do_close)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()

        if 'hidden' in options and self.window is None:
            self.window_hidden = True

        self.activate()
        return 0

    def on_open(self, action, param):
        self.window.open_audio()

    def on_playpause(self, action=None, param=None):
        # Reverse self.playing bool value
        self.playing = False if self.playing else True

        # Change mainplayer playing
        self.mainplayer.set_property('playing', self.playing)

        # Update window elements to new playing state
        self.window.update_playing_ui(self.playing)

    def on_background(self, action, value):
        action.set_state(GLib.Variant('b', value))
        self.gsettings.set_boolean('background-playback', value)
        if value:
            self.window.quit_revealer.set_reveal_child(True)
        else:
            self.window.quit_revealer.set_reveal_child(False)

    def on_shortcuts(self, action, param):
        window = Gtk.Builder.new_from_resource(
            '/com/rafaelmardojai/Blanket/shortcuts.ui'
        ).get_object('shortcuts')
        window.set_transient_for(self.window)
        window.props.section_name = 'shortcuts'
        window.set_modal(True)
        window.present()

    def on_about(self, action, param):
        dialog = AboutDialog(self.version)
        dialog.set_transient_for(self.window)
        dialog.set_modal(True)
        dialog.present()

    def on_close(self, action, param):
        self.window.close()

    def on_quit(self, action, param):
        self.quit()

    def _do_close(self, widget, event):
        background = self.gsettings.get_value('background-playback')

        if background:
            return widget.hide_on_delete()
        else:
            self.quit()

def main(version):
    app = Application(version)
    return app.run(sys.argv)
