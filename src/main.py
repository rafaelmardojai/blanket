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
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Handy', '1')

from gettext import gettext as _
from gi.repository import GLib, Gst, Gdk, Gio, Gtk, Handy

from .window import BlanketWindow
from .about import AboutDialog


class Application(Gtk.Application):
    def __init__(self, version):
        super().__init__(application_id='com.rafaelmardojai.Blanket',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        GLib.set_application_name(_('Blanket'))
        GLib.setenv("PULSE_PROP_application.icon_name",
                    "com.rafaelmardojai.Blanket-symbolic", True)

        self.window = None
        self.version = version

    def do_startup(self):
        # Startup application
        Gtk.Application.do_startup(self)
        self.setup_actions()
        self.load_css()

        # Init GStreamer
        Gst.init()
        # Init Handy
        Handy.init()

    def setup_actions(self):
        # Add open action
        open_action = Gio.SimpleAction.new('open', None)
        open_action.connect('activate', self.on_open)
        self.add_action(open_action)
        self.set_accels_for_action('app.open', ['<Ctl>o'])

        # Add about action
        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', self.on_about)
        self.add_action(about_action)

    def load_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource('/com/rafaelmardojai/Blanket/style.css')
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def do_activate(self):
        self.window = self.props.active_window
        if not self.window:
            self.window = BlanketWindow(application=self)
        self.window.present()

    def on_open(self, action, param):
        self.window.open_audio()

    def on_about(self, action, param):
        dialog = AboutDialog(self.version)
        dialog.set_transient_for(self.window)
        dialog.set_modal(True)
        dialog.present()
        dialog.show_all()

def main(version):
    app = Application(version)
    return app.run(sys.argv)
