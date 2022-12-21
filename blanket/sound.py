# Copyright 2020-2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gi.repository import Gio, GObject, Gtk, Gst, GstPlay

from blanket.settings import Settings


SOUNDS = [
    {
        'name': _('Nature'),
        'sounds': [
            {
                'name': 'rain',
                'title': _('Rain')
            },
            {
                'name': 'storm',
                'title': _('Storm')
            },
            {
                'name': 'wind',
                'title': _('Wind')
            },
            {
                'name': 'waves',
                'title': _('Waves')
            },
            {
                'name': 'stream',
                'title': _('Stream')
            },
            {
                'name': 'birds',
                'title': _('Birds')
            },
            {
                'name': 'summer-night',
                'title': _('Summer Night')
            }
        ]
    },
    {
        'name': _('Travel'),
        'sounds': [
            {
                'name': 'train',
                'title': _('Train')
            },
            {
                'name': 'boat',
                'title': _('Boat')
            },
            {
                'name': 'city',
                'title': _('City')
            }
        ]
    },
    {
        'name': _('Interiors'),
        'sounds': [
            {
                'name': 'coffee-shop',
                'title': _('Coffee Shop')
            },
            {
                'name': 'fireplace',
                'title': _('Fireplace')
            }
        ]
    },
    {
        'name': _('Noise'),
        'sounds': [
            {
                'name': 'pink-noise',
                'title': _('Pink Noise')
            },
            {
                'name': 'white-noise',
                'title': _('White Noise')
            }
        ]
    }
]


class MainPlayer(GObject.GObject, Gio.ListModel):
    """
    Virtual app sounds player

    It also implements Gio.ListModel and stores the app sound list.
    """
    _instance = None
    _cookie = 0
    _sounds = []  # SoundObject list

    __gtype_name__ = 'MainPlayer'
    __gsignals__ = {
        'preset-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'reset-volumes': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    playing = GObject.Property(type=bool, default=True)
    volume = GObject.Property(type=float, default=0)

    @classmethod
    def get(cls):
        """Return an active instance of Settings."""
        if cls._instance is None:
            cls._instance = MainPlayer()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.connect('notify::playing', self._on_playing)

    def populate_sounds(self):
        """
        Populate default and saved sounds
        """

        # Self populate
        for g in SOUNDS:
            # Iterate sounds
            for s in g['sounds']:
                # Create a new SoundObject
                sound = SoundObject(s['name'], title=s['title'])
                self.append(sound)

        # Load saved custom audios
        for name, uri in Settings.get().custom_audios.items():
            # Create a new SoundObject
            sound = SoundObject(name, uri=uri, custom=True)
            self.append(sound)

    def mute_vol_zero(self):
        for sound in self:
            if sound.saved_volume == 0:
                sound.playing = False

    def preset_changed(self):
        self.playing = True
        self.emit('preset-changed')

    def reset_volumes(self):
        self.emit('reset-volumes')

    def _on_playing(self, _player, _param):
        """
        Toggle suspension inhibition when playing
        """
        app = Gtk.Application.get_default()

        if self.playing:
            self._cookie = app.inhibit(
                None,
                Gtk.ApplicationInhibitFlags.SUSPEND,
                'Playback in progress'
            )
        elif self._cookie != 0:
            app.uninhibit(self._cookie)

    """
    ListModel methods
    """

    def __iter__(self):
        return iter(self._sounds)

    def do_get_item(self, position):
        return self._sounds[position]

    def do_get_item_type(self):
        return SoundObject

    def do_get_n_items(self):
        return len(self._sounds)

    def append(self, sound):
        if isinstance(sound, SoundObject):
            self._sounds.append(sound)
            self.items_changed(len(self._sounds) - 1, 0, 1)

    def remove(self, position):
        del self._sounds[position]
        self.items_changed(position, 1, 0)


class SoundObject(GObject.Object):
    """
    Describe a sound with it's properties
    """
    __gtype_name__ = 'SoundObject'

    playing = GObject.Property(type=bool, default=False)
    title = GObject.Property(type=str)
    icon_name = GObject.Property(type=str)

    def __init__(self, name, uri=None, title=None, custom=False, **kwargs):
        super().__init__(**kwargs)

        resource_tmpl = 'resource:/com/rafaelmardojai/Blanket/sounds/{}.ogg'
        icon_tmpl = 'com.rafaelmardojai.Blanket-{}'

        self._player = None

        self.name = name
        self.uri = uri if uri else resource_tmpl.format(name)
        self.title = title if title else name
        self.icon_name = icon_tmpl.format('sound-wave' if custom else name)
        self.custom = custom

        self.connect('notify::playing', self._playing_changed)
        # Set saved playing state
        if not self.saved_mute:
            self.playing = not self.saved_mute

        # Connect mainplayer reset-volumes signal
        MainPlayer.get().connect(
            'reset-volumes',
            self._on_reset_volumes
        )

    @property
    def player(self):
        if self._player is None:
            self._player = SoundPlayer(self)
        return self._player

    @GObject.Property(type=float)
    def saved_volume(self):
        return Settings.get().get_sound_volume(self.name)

    @saved_volume.setter
    def saved_volume(self, volume):
        volume = round(volume, 2)
        self.player.set_virtual_volume(volume)
        Settings.get().set_sound_volume(self.name, volume)

    @property
    def saved_mute(self):
        return Settings.get().get_sound_mute(self.name)

    @saved_mute.setter
    def saved_mute(self, mute):
        Settings.get().set_sound_mute(self.name, mute)

    def remove(self):
        if self.custom:
            Settings.get().remove_custom_audio(self.name)

    def _playing_changed(self, _object, _pspec):
        # Toggle player mute state
        if self.playing:
            if self.saved_volume > 0:
                self.player.set_virtual_volume(self.saved_volume)
            else:
                self.player.set_virtual_volume(0.5)
                self.saved_volume = 0.5
        else:
            self.player.set_virtual_volume(0)

        self.saved_mute = not self.playing  # Save playing state

    def _on_reset_volumes(self, _player):
        self.saved_volume = 0.0
        self.playing = False


class SoundPlayer(GstPlay.Play):
    """
    GstPlayer.Player with modifications
    """
    __gtype_name__ = 'SoundPlayer'

    def __init__(self, sound):
        super().__init__()
        self.sound = sound
        # Create a var to save saved volume
        self.saved_volume = 0.0
        # Always start with volume in 0
        self.set_volume(0)

        # Set SoundObject.uri as player uri
        self.set_uri(self.sound.uri)
        self.name = self.sound.name

        # Loop setup
        self.prerolled = False
        self.pipeline = self.get_pipeline()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_bus_message)

        # Connect mainplayer volume signal
        self.volume_hdlr = MainPlayer.get().connect(
            'notify::volume',
            self._on_main_volume_changed)
        # Connect mainplayer muted signal
        self.playing_hdlr = MainPlayer.get().connect(
            'notify::playing',
            self._on_playing_changed)

        # Connect volume-changed signal
        self.connect('notify::volume', self._on_volume_changed)

    def set_virtual_volume(self, volume):
        # Get last saved sound volume
        self.saved_volume = volume
        # Multiply sound volume with mainplayer volume
        volume = self.saved_volume * MainPlayer.get().volume
        # Set final volume to player
        self.set_volume(volume)

    def remove(self):
        # Stop player
        self.stop()
        # Disconnect main player signals
        MainPlayer.get().disconnect(self.volume_hdlr)
        MainPlayer.get().disconnect(self.playing_hdlr)

    def _on_playing_changed(self, _player, _volume):
        if not self.__vol_zero():
            if MainPlayer.get().playing:
                self.play()
            else:
                self.pause()

    def _on_volume_changed(self, _player, _volume):
        # Fix external changes to player volume
        volume = self.saved_volume * MainPlayer.get().volume
        if volume > 0 and self.get_volume() == 0.0:
            self.set_volume(volume)
            return
        # Only play if volume > 0
        if self.__vol_zero():
            self.pause()
        elif MainPlayer.get().playing:
            self.play()

    def _on_main_volume_changed(self, _player, _volume):
        if not self.__vol_zero(self.sound.saved_volume):
            # Set volume again when mainplayer volume changes
            self.set_virtual_volume(self.saved_volume)

    def _on_bus_message(self, _bus, message):
        if message:
            if message.type is Gst.MessageType.SEGMENT_DONE:
                self.pipeline.seek_simple(
                    Gst.Format.TIME,
                    Gst.SeekFlags.SEGMENT,
                    0
                )

            if message.type is Gst.MessageType.ASYNC_DONE:
                if not self.prerolled:
                    self.pipeline.seek_simple(
                        Gst.Format.TIME,
                        Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT,
                        0
                    )
                    self.prerolled = True

            return True

    def __vol_zero(self, volume=None):
        volume = volume if volume else self.get_volume()
        return True if volume == 0 else False
