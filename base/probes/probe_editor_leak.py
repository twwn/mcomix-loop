"""How much does each opened and closed archive editor keep alive, and
through what?  Built on MComixTest; run under xvfb-run with a timeout.
"""
import gc
import os
import sys
import unittest

sys.path.insert(0, '/tmp/mcomix-git')

import test  # noqa: E402
from test import MComixTest, get_testfile_path, pump, wait_for  # noqa: E402

from mcomix import constants, edit_dialog, icons, main  # noqa: E402

CYCLES = int(os.environ.get('CYCLES', '6'))
BOOK = os.environ.get('BOOK', os.path.join(
    os.path.dirname(get_testfile_path('archives', '01-ZIP-Normal.zip')),
    '..', 'pepper-and-carrot', 'Pepper-and-Carrot_E01_The-Potion-of-Flight.cbz'))


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
        window = main.MainWindow(open_path=os.path.abspath(BOOK))
        main.set_main_window(window)
        wait_for(lambda: window.imagehandler.get_number_of_pages() > 0,
                 seconds=20)
        print('pages:', window.imagehandler.get_number_of_pages(), flush=True)
        try:
            for cycle in range(CYCLES):
                dialog = edit_dialog._EditArchiveDialog(window)
                grid = dialog._image_area._grid
                wait_for(lambda: grid.get_n_items() >= window.imagehandler.get_number_of_pages()
                         if hasattr(grid, 'get_n_items') else True, seconds=10)
                wait_for(lambda: False, seconds=1.5)   # let thumbnails arrive
                dialog.destroy()
                edit_dialog._close_dialog()
                if os.environ.get('DISPOSE') == 'tree':
                    stack, tree = [dialog], []
                    while stack:
                        w = stack.pop()
                        tree.append(w)
                        c = w.get_first_child()
                        while c is not None:
                            stack.append(c)
                            c = c.get_next_sibling()
                    for w in tree:
                        w.run_dispose()
                    del stack, tree, w, c
                elif os.environ.get('DISPOSE'):
                    dialog.run_dispose()
                del dialog, grid
                for _ in range(3):
                    pump()
                    gc.collect()
                from mcomix import thumbnail_list
                items = [o for o in gc.get_objects()
                         if type(o) is thumbnail_list.ThumbnailItem]
                print('cycle %d: rss %d KiB, live editors %d, items %d, with thumbnail %d'
                      % (cycle, rss_kib(), live(edit_dialog._EditArchiveDialog),
                         len(items), sum(1 for i in items if i.thumbnail is not None)),
                      flush=True)
                del items
            if os.environ.get('REFERRERS'):
                d = next(o for o in gc.get_objects()
                         if type(o) is edit_dialog._EditArchiveDialog)
                for r in gc.get_referrers(d):
                    if r is sys._getframe():
                        continue
                    desc = type(r).__name__
                    if isinstance(r, dict):
                        keys = [k for k, v in r.items() if v is d]
                        desc += ' keys=%s' % keys
                        owners = [type(o).__name__ for o in gc.get_referrers(r)
                                  if getattr(o, '__dict__', None) is r]
                        desc += ' of %s' % owners
                    elif hasattr(r, '__func__'):
                        desc += ' %s' % r.__func__.__qualname__
                    elif isinstance(r, (list, tuple)):
                        desc += ' len=%d' % len(r)
                    print('  referrer:', desc[:200], flush=True)
        finally:
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump()


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=0).result
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0 if result.wasSuccessful() else 1)
