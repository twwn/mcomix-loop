"""Is a closed library window collected?  Opens and closes it CYCLES
times, with BOOKS copies of a book in the library, and reports RSS and
the live _LibraryDialog and cover count.  Built on MComixTest.
"""
import gc
import os
import shutil
import sys
import unittest

sys.path.insert(0, '/tmp/mcomix-git')

import test  # noqa: E402
from test import MComixTest, get_testfile_path, pump, wait_for  # noqa: E402

from mcomix import constants, icons, main  # noqa: E402
from mcomix.library import main_dialog  # noqa: E402

CYCLES = int(os.environ.get('CYCLES', '5'))
BOOKS = int(os.environ.get('BOOKS', '0'))
SOURCE = os.environ.get('BOOK', '/tmp/mcomix-loop-scratch/big60.cbz')


def rss_kib():
    with open('/proc/self/statm') as fp:
        return int(fp.read().split()[1]) * os.sysconf('SC_PAGE_SIZE') // 1024


def live(cls):
    return sum(1 for o in gc.get_objects() if type(o) is cls)


class Probe(MComixTest):

    def test_probe(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow(
            open_path=get_testfile_path('archives', '01-ZIP-Normal.zip'))
        main.set_main_window(window)
        wait_for(lambda: window.imagehandler.get_number_of_pages() > 0,
                 seconds=20)
        try:
            if BOOKS:
                books = os.path.join(self.tmp_dir, 'books')
                os.makedirs(books)
                paths = []
                for i in range(BOOKS):
                    path = os.path.join(books, 'book%03d.cbz' % i)
                    shutil.copy(SOURCE, path)
                    paths.append(path)
                main_dialog.open_dialog(None, window)
                pump()
                main_dialog._dialog.backend.add_book  # noqa: B018
                for path in paths:
                    main_dialog._dialog.backend.add_book(path)
                main_dialog._close_dialog()
                pump()
            for cycle in range(CYCLES):
                main_dialog.open_dialog(None, window)
                dialog = main_dialog._dialog
                wait_for(lambda: False, seconds=2.5)   # covers load
                del dialog
                main_dialog._close_dialog()
                for _ in range(3):
                    pump()
                    gc.collect()
                print('cycle %d: rss %d KiB, live library windows %d'
                      % (cycle, rss_kib(), live(main_dialog._LibraryDialog)),
                      flush=True)
        finally:
            main_dialog._close_dialog()
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump()


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=0).result
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0 if result.wasSuccessful() else 1)
