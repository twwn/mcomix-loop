"""Copy of ../probe_editor_leak.py with its counting checked.

Differences: the tree is TREE (not hard-wired /tmp/mcomix-git); a
baseline before the first editor; ThumbnailItems split into the editor's
(uid is a path) and the main window sidebar's (uid is a page number);
the wait for pages uses grid.store (the grid has no get_n_items, so the
original's wait was a no-op), then waits until the editor's thumbnail
count stops changing.
"""
import gc
import os
import sys
import unittest

TREE = os.environ['TREE']
sys.path.insert(0, TREE)

from test import MComixTest, pump, wait_for  # noqa: E402
from mcomix import constants, edit_dialog, icons, main, thumbnail_list  # noqa: E402

CYCLES = int(os.environ.get('CYCLES', '4'))
BOOK = os.environ['BOOK']


def counts():
    items = [o for o in gc.get_objects()
             if type(o) is thumbnail_list.ThumbnailItem]
    ed = [i for i in items if isinstance(i.uid, str)]
    sb = [i for i in items if not isinstance(i.uid, str)]
    return (len(items), sum(i.thumbnail is not None for i in items),
            len(ed), sum(i.thumbnail is not None for i in ed),
            len(sb), sum(i.thumbnail is not None for i in sb))


def live(cls):
    return sum(1 for o in gc.get_objects() if type(o) is cls)


class Probe(MComixTest):

    def test_probe(self):
        print('edit_dialog from', edit_dialog.__file__, flush=True)
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow(open_path=os.path.abspath(BOOK))
        main.set_main_window(window)
        n = None
        wait_for(lambda: window.imagehandler.get_number_of_pages() > 0,
                 seconds=20)
        n = window.imagehandler.get_number_of_pages()
        wait_for(lambda: False, seconds=1.5)
        for _ in range(3):
            pump()
            gc.collect()
        fmt = ('%-9s live editors %d | all items %d with thumb %d | '
               'editor items %d with thumb %d | sidebar items %d with thumb %d')
        print('pages:', n, flush=True)
        print(fmt % (('baseline', live(edit_dialog._EditArchiveDialog))
                     + counts()), flush=True)
        try:
            for cycle in range(CYCLES):
                dialog = edit_dialog._EditArchiveDialog(window)
                grid = dialog._image_area._grid
                filled = wait_for(lambda: grid.store.get_n_items() >= n,
                                  seconds=10)
                last = [-1, 0]

                def settled():
                    got = sum(1 for i in range(grid.store.get_n_items())
                              if grid.store.get_item(i).thumbnail is not None)
                    if got == last[0]:
                        last[1] += 1
                    else:
                        last[:] = [got, 0]
                    return got > 0 and last[1] > 200
                wait_for(settled, seconds=8)
                open_thumbs = last[0]
                dialog.destroy()
                edit_dialog._close_dialog()
                del dialog, grid
                for _ in range(3):
                    pump()
                    gc.collect()
                print(fmt % (('cycle %d' % cycle,
                              live(edit_dialog._EditArchiveDialog))
                             + counts())
                      + ' | store filled %s, thumbs while open %d'
                      % (filled, open_thumbs), flush=True)
        finally:
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump()


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], 'Probe'], exit=False)
    sys.stdout.flush()
    os._exit(0)
