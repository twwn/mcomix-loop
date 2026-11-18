"""Time opening the library window over a library of BOOKS books (env,
default 10000), none of whose files exist, and the first steps a reader
takes in it: the first frame, a search, the search cleared, a sort by
name and by date added, and closing.  PROFILE=<step> adds cProfile's
top 30 of that step (open, search, clear, sort name, sort added, close)
in the last round, by cumulative time.

Copy to test/_bench_library_open.py and run under xvfb:
    python3 -m pytest test/_bench_library_open.py -q -s -p no:warnings
"""

import cProfile
import os
import pstats
import sqlite3
import statistics
import time

from gi.repository import Gtk

from mcomix import constants, icons, main
from mcomix.library import backend, main_dialog
from mcomix.preferences import prefs

from . import MComixTest, pump, wait_frames

BOOKS = int(os.environ.get('BOOKS', '10000'))
ROUNDS = int(os.environ.get('ROUNDS', '5'))


def _ms(start):
    return 1000 * (time.perf_counter() - start)


class Bench(MComixTest):

    def test_bench(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow()
        main.set_main_window(window)
        pump()
        # Create the database, then fill it behind the backend's back.
        main_dialog.open_dialog(None, window)
        pump()
        main_dialog._close_dialog()
        pump()
        backend._backend = None
        con = sqlite3.connect(constants.LIBRARY_DATABASE_PATH)
        con.executemany(
            'insert into book (name, path, pages, format, size) '
            'values (?, ?, 20, 1, 1000)',
            [('Book %05d.cbz' % i, '/nowhere/shelf %02d/Book %05d.cbz'
              % (i % 50, i)) for i in range(BOOKS)])
        con.commit()
        con.close()

        # The collection the library opens on: left at its default,
        # None, it opens on none and shows no covers.
        prefs['last library collection'] = constants.COLLECTION_ALL
        rows = {name: [] for name in ('open', 'frame', 'covers', 'search',
                                      'clear',
                                      'sort name', 'sort added', 'close')}
        # PROFILE=<one of the rows> profiles that step of the last round.
        wanted = os.environ.get('PROFILE')
        profile = cProfile.Profile()

        def step(name, last, action):
            start = time.perf_counter()
            if last and name == wanted:
                profile.enable()
            action()
            if last and name == wanted:
                profile.disable()
            rows[name].append(_ms(start))

        for round_ in range(ROUNDS):
            last = round_ == ROUNDS - 1
            backend._backend = None
            start = time.perf_counter()
            step('open', last, lambda: main_dialog.open_dialog(None, window))
            dialog = main_dialog._dialog
            wait_frames(dialog, frames=2, seconds=10)
            rows['frame'].append(_ms(start))
            # The covers come from an idle, after the first frames: a
            # search typed before it ran would replace that display.
            deadline = time.monotonic() + 10
            while (not dialog.book_area._covers.store.get_n_items()
                   and time.monotonic() < deadline):
                pump(seconds=0.01)
            rows['covers'].append(_ms(start))
            entry = dialog.control_area.search_entry

            def search(text):
                entry.set_text(text)
                entry.emit('activate')
                pump()
            step('search', last, lambda: search('Book 012'))
            step('clear', last, lambda: search(''))
            for key, label in ((constants.SORT_NAME, 'sort name'),
                               (constants.SORT_LAST_MODIFIED, 'sort added')):
                def resort(key=key):
                    # What the sort menu's action does.
                    prefs['lib sort key'] = key
                    dialog.book_area.set_sort_order()
                    pump()
                step(label, last, resort)

            def close():
                main_dialog._close_dialog()
                pump()
            step('close', last, close)
        print('\n%d books, %d rounds' % (BOOKS, ROUNDS))
        for name, times in rows.items():
            print('%-10s median %7.1f ms  min %7.1f  max %7.1f' % (
                name, statistics.median(times), min(times), max(times)))
        if wanted:
            pstats.Stats(profile).sort_stats('cumulative').print_stats(
                'mcomix', 30)
        for toplevel in Gtk.Window.list_toplevels():
            if isinstance(toplevel, main_dialog._LibraryDialog):
                toplevel.destroy()
        window.terminate_program()
        window.destroy()
        main.set_main_window(None)
        pump()
