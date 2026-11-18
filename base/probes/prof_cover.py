"""Profile one warm cover on one thread: _BookArea._get_pixbuf for each
book, stored covers on disk, memory cache emptied."""
import cProfile
import os
import pstats
import sys
import time
import unittest

sys.path.insert(0, os.getcwd())
from test import MComixTest, wait_for, pump  # noqa: E402
from mcomix import constants, icons, keybindings, main  # noqa: E402
from mcomix.library import backend as library_backend  # noqa: E402
from mcomix.library.pixbuf_cache import get_pixbuf_cache  # noqa: E402
from mcomix.preferences import prefs  # noqa: E402

BOOKS_DIR = os.environ['BOOKS_DIR']
COUNT = int(os.environ.get('BOOKS', '200'))


class Probe(MComixTest):
    def test_profile(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        keybindings._manager = None
        prefs['library cover size'] = int(os.environ.get('COVER', '125'))
        prefs['show library without book'] = True
        paths = sorted(os.path.join(BOOKS_DIR, n) for n in os.listdir(BOOKS_DIR))[:COUNT]
        backend = library_backend.LibraryBackend()
        with backend.transaction():
            for path in paths:
                backend.add_book(path)
        window = main.MainWindow()
        main.set_main_window(window)
        try:
            wait_for(lambda: window._shelf is not None and window._shelf.get_visible(), 20)
            area = window._shelf.book_area
            area.stop_update()
            ids = [backend.get_book_by_path(p).id for p in paths]
            for uid in ids:   # store every cover
                area._get_pixbuf(uid)
            for label in ('warm', 'warm again'):
                get_pixbuf_cache().invalidate_all()
                begun = time.perf_counter()
                for uid in ids:
                    area._get_pixbuf(uid)
                print('%s: %.2f ms per cover, one thread' % (
                    label, (time.perf_counter() - begun) / len(ids) * 1000), flush=True)
            begun = time.perf_counter()
            for uid in ids:
                area._get_pixbuf(uid)
            print('memory cache hit: %.3f ms per cover' % (
                (time.perf_counter() - begun) / len(ids) * 1000), flush=True)
            get_pixbuf_cache().invalidate_all()
            profile = cProfile.Profile()
            profile.enable()
            for uid in ids:
                area._get_pixbuf(uid)
            profile.disable()
            stats = pstats.Stats(profile, stream=sys.stdout)
            stats.sort_stats('cumulative').print_stats(45)
        finally:
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump()


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], 'Probe'], exit=False)
    sys.stdout.flush()
    os._exit(0)
