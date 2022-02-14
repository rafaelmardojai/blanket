# Forked from:
# https://gitlab.gnome.org/World/lollypop/-/blob/master/lollypop/mpris.py
#
# Copyright (c) 2014-2020 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (c) 2016 Gaurav Narula
# Copyright (c) 2016 Felipe Borges <felipeborges@gnome.org>
# Copyright (c) 2013 Arnel A. Borja <kyoushuu@yahoo.com>
# Copyright (c) 2013 Vadim Rutkovsky <vrutkovs@redhat.com>
# Copyright (c) 2020 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gi.repository import Gio, GLib, Gtk

from random import randint


class Server:

    def __init__(self, con, path):
        method_outargs = {}
        method_inargs = {}
        for interface in Gio.DBusNodeInfo.new_for_xml(self.__doc__).interfaces:

            for method in interface.methods:
                method_outargs[method.name] = "(" + "".join(
                              [arg.signature for arg in method.out_args]) + ")"
                method_inargs[method.name] = tuple(
                    arg.signature for arg in method.in_args)

            con.register_object(object_path=path,
                                interface_info=interface,
                                method_call_closure=self.on_method_call)

        self.method_inargs = method_inargs
        self.method_outargs = method_outargs

    def on_method_call(self,
                       connection,
                       sender,
                       object_path,
                       interface_name,
                       method_name,
                       parameters,
                       invocation):

        args = list(parameters.unpack())
        for i, sig in enumerate(self.method_inargs[method_name]):
            if sig == "h":
                msg = invocation.get_message()
                fd_list = msg.get_unix_fd_list()
                args[i] = fd_list.get(args[i])

        try:
            result = getattr(self, method_name)(*args)

            # out_args is atleast (signature1).
            # We therefore always wrap the result as a tuple.
            # Refer to https://bugzilla.gnome.org/show_bug.cgi?id=765603
            result = (result,)

            out_args = self.method_outargs[method_name]
            if out_args != "()":
                variant = GLib.Variant(out_args, result)
                invocation.return_value(variant)
            else:
                invocation.return_value(None)
        except Exception as e:
            print(e)


class MPRIS(Server):
    """
    <!DOCTYPE node PUBLIC
    "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
    "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
    <node>
        <interface name="org.freedesktop.DBus.Introspectable">
            <method name="Introspect">
                <arg name="data" direction="out" type="s"/>
            </method>
        </interface>
        <interface name="org.freedesktop.DBus.Properties">
            <method name="Get">
                <arg name="interface" direction="in" type="s"/>
                <arg name="property" direction="in" type="s"/>
                <arg name="value" direction="out" type="v"/>
            </method>
            <method name="Set">
                <arg name="interface_name" direction="in" type="s"/>
                <arg name="property_name" direction="in" type="s"/>
                <arg name="value" direction="in" type="v"/>
            </method>
            <method name="GetAll">
                <arg name="interface" direction="in" type="s"/>
                <arg name="properties" direction="out" type="a{sv}"/>
            </method>
        </interface>
        <interface name="org.mpris.MediaPlayer2">
            <method name="Raise">
            </method>
            <method name="Quit">
            </method>
            <property name="CanQuit" type="b" access="read" />
            <property name="CanRaise" type="b" access="read" />
            <property name="Identity" type="s" access="read"/>
            <property name="DesktopEntry" type="s" access="read"/>
        </interface>
        <interface name="org.mpris.MediaPlayer2.Player">
            <method name="PlayPause"/>
            <property name="PlaybackStatus" type="s" access="read"/>
            <property name="Metadata" type="a{sv}" access="read">
            </property>
            <property name="Volume" type="d" access="readwrite"/>
            <property name="CanPlay" type="b" access="read"/>
            <property name="CanPause" type="b" access="read"/>
            <property name="CanControl" type="b" access="read"/>
        </interface>
    </node>
    """
    __MPRIS_IFACE = "org.mpris.MediaPlayer2"
    __MPRIS_PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
    __MPRIS_BLANKET = "org.mpris.MediaPlayer2.Blanket"
    __MPRIS_PATH = "/org/mpris/MediaPlayer2"

    def __init__(self, app):
        self.app = app

        self.__metadata = {}

        track_id = 0 + randint(10000000, 90000000)
        self.__metadata["mpris:trackid"] = GLib.Variant(
            "o",
            "/com/rafaelmardojai/Blanket/Track/%s" % track_id)
        self.__metadata["xesam:title"] = GLib.Variant(
            "s", _("Listen to different sounds")
        )
        self.__metadata["xesam:album"] = GLib.Variant(
            "s", _("Listen to different sounds")
        )
        self.__metadata["xesam:artist"] = GLib.Variant("as", [_("Blanket")])

        self.__bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        Gio.bus_own_name_on_connection(self.__bus,
                                       self.__MPRIS_BLANKET,
                                       Gio.BusNameOwnerFlags.NONE,
                                       None,
                                       None)
        Server.__init__(self, self.__bus, self.__MPRIS_PATH)

        self.app.mainplayer.connect(
            "notify::playing", self._on_playing_changed
        )
        self.app.mainplayer.connect("notify::volume", self._on_volume_changed)

    def Raise(self):
        self.app.window.present_with_time(Gtk.get_current_event_time())

    def Quit(self):
        self.app.quit()

    def PlayPause(self):
        self.app.on_playpause()

    def Get(self, interface, property_name):
        if property_name in [
            "CanQuit", "CanRaise", "CanControl", "CanPlay", "CanPause"
        ]:
            return GLib.Variant("b", True)
        elif property_name == "Identity":
            return GLib.Variant("s", "Blanket")
        elif property_name == "DesktopEntry":
            return GLib.Variant("s", "com.rafaelmardojai.Blanket")
        elif property_name == "PlaybackStatus":
            return GLib.Variant("s", self._get_status())
        elif property_name == "Metadata":
            return GLib.Variant("a{sv}", self.__metadata)
        elif property_name == "Volume":
            return GLib.Variant(
                "d", self.app.mainplayer.volume
            )
        else:
            return GLib.Variant("b", False)

    def GetAll(self, interface):
        ret = {}
        if interface == self.__MPRIS_IFACE:
            for property_name in ["CanQuit",
                                  "CanRaise",
                                  "Identity",
                                  "DesktopEntry"]:
                ret[property_name] = self.Get(interface, property_name)
        elif interface == self.__MPRIS_PLAYER_IFACE:
            for property_name in ["PlaybackStatus",
                                  "Metadata",
                                  "Volume",
                                  "CanPlay",
                                  "CanPause",
                                  "CanControl"]:
                ret[property_name] = self.Get(interface, property_name)
        return ret

    def Set(self, interface, property_name, new_value):
        if property_name == "Volume":
            self.app.mainplayer.volume = new_value

    def PropertiesChanged(self, interface_name, changed_properties,
                          invalidated_properties):
        self.__bus.emit_signal(None,
                               self.__MPRIS_PATH,
                               "org.freedesktop.DBus.Properties",
                               "PropertiesChanged",
                               GLib.Variant.new_tuple(
                                   GLib.Variant("s", interface_name),
                                   GLib.Variant("a{sv}", changed_properties),
                                   GLib.Variant("as", invalidated_properties)))

    def Introspect(self):
        return self.__doc__

    def update_title(self, title):
        # Used when changing presets
        self.__metadata["xesam:title"] = GLib.Variant("s", _(title))
        changed_properties = {"Metadata": GLib.Variant("a{sv}", self.__metadata)}
        self.PropertiesChanged(self.__MPRIS_PLAYER_IFACE, changed_properties, [])

    def _get_status(self):
        playing = self.app.mainplayer.playing
        if playing:
            return "Playing"
        else:
            return "Paused"

    def _on_volume_changed(self, player, volume):
        self.PropertiesChanged(
            self.__MPRIS_PLAYER_IFACE,
            {
                "Volume": GLib.Variant(
                    "d",
                    self.app.mainplayer.volume
                ),
            },
            []
        )

    def _on_playing_changed(self, player, playing):
        properties = {"PlaybackStatus": GLib.Variant("s", self._get_status())}
        self.PropertiesChanged(self.__MPRIS_PLAYER_IFACE, properties, [])
