"""Probe: leave fullscreen from a maximized window, logging every state change."""
import os
import sys
import time

from gi.repository import GLib

from mcomix import constants, icons, keybindings, main
from mcomix.preferences import prefs

from . import MComixTest

LOG = os.environ.get('FSMAX_LOG', 'fsmax.log')


def log(*args):
    with open(LOG, 'a') as f:
        f.write(' '.join(str(a) for a in args) + '\n')


def pump_for(seconds):
    ctx = GLib.MainContext.default()
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        ctx.iteration(False)
        time.sleep(0.005)


class FsMaxProbe(MComixTest):

    def test_probe(self):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        keybindings._manager = None
        w = main.MainWindow()
        main.set_main_window(w)
        orig = w.restore_window_geometry
        def traced():
            log('restore_window_geometry: size', w.get_window_size(), 'max', w.is_maximized(),
                'prefs', prefs['window width'], prefs['window height'], prefs['window maximized'])
            r = orig()
            log('  ->', r)
            return r
        w.restore_window_geometry = traced
        omax = w.maximize
        def tmax():
            log('maximize() called; fs', w.is_fullscreen(), 'max', w.is_maximized())
            omax()
        w.maximize = tmax
        for prop in ('fullscreened', 'maximized', 'default-width', 'default-height'):
            w.connect('notify::' + prop, lambda o, p: log('notify', p.name, 'fs', o.is_fullscreen(),
                                                         'max', o.is_maximized(), 'size', o.get_width(), o.get_height()))
        pump_for(1)
        log('start size', w.get_width(), w.get_height())
        w.maximize()
        pump_for(2)
        log('after maximize', w.is_maximized(), w.get_width(), w.get_height())
        act = w.actiongroup.get_action('fullscreen')
        act.set_active(True)
        pump_for(2)
        log('after fullscreen', w.is_fullscreen(), w.is_maximized(), w.get_width(), w.get_height())
        act.set_active(False)
        pump_for(4)
        log('after unfullscreen', w.is_fullscreen(), w.is_maximized(), w.get_width(), w.get_height())
        log('done')
        sys.stdout.flush()
        w.terminate_program()
        w.destroy()
        main.set_main_window(None)
        pump_for(0.5)
