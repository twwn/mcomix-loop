"""Time the walks over the main window's menus: watch_menu_clicks() on
the menu bar and the right-click menu, and the full rebuild of both.

Copy to test/_bench_menu_walk.py and run under xvfb:
    python3 -m pytest test/_bench_menu_walk.py -q -s -p no:warnings
"""

import os
import statistics
import sys
import time

from mcomix import constants, icons, keybindings, main, widgets
from mcomix.preferences import prefs

from . import MComixTest, pump

ROUNDS = 200


def _median_ms(function, rounds=ROUNDS):
    times = []
    for _ in range(rounds):
        start = time.perf_counter()
        function()
        times.append(time.perf_counter() - start)
    return 1000 * statistics.median(times)


class Bench(MComixTest):

    def test_bench(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        prefs['show menubar'] = True
        icons.load_icons()
        keybindings._manager = None
        window = main.MainWindow()
        main.set_main_window(window)
        pump(2000)
        ui = window.uimanager
        widgets_in = sum(1 for _ in widgets._descendants(window))
        popovers = len(list(widgets._menu_popovers(ui.menubar))
                       + list(widgets._menu_popovers(ui.popup)))

        def watch():
            widgets.watch_menu_clicks(ui.menubar)
            widgets.watch_menu_clicks(ui.popup)
        print('\nwidgets %d, menu popovers %d' % (widgets_in, popovers))
        print('walk window %.2f ms' % _median_ms(
            lambda: sum(1 for _ in widgets._descendants(window))))
        print('watch both %.2f ms' % _median_ms(watch))
        print('rebuild menus %.2f ms' % _median_ms(ui._rebuild_menus, 50))
        layouts = sys.modules[type(ui).__module__]
        print('menu bar model %.2f ms' % _median_ms(
            lambda: ui._build(layouts._MENUBAR), 50))
        print('menu bar set %.2f ms' % _median_ms(
            lambda: ui.menubar.set_menu_model(ui._build(layouts._MENUBAR)),
            50))
        print('popup set %.2f ms' % _median_ms(
            lambda: ui.popup.set_menu_model(
                ui._build(layouts._POPUP, hide_disabled=True)), 50))
        print('bookmarks refresh %.2f ms' % _median_ms(ui.bookmarks.refresh,
                                                      50))
        window.terminate_program()
        window.destroy()
        main.set_main_window(None)
        pump(2000)
