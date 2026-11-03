"""How long display_covers() holds the main thread behind real cover reads."""
import glob, os, shutil, statistics, threading, time, unittest.mock
from test import pump, wait_for, get_testfile_path
from test import test_library_dialog as _t
from mcomix import constants

SLOW = os.environ['SLOW_DIR']
BOOKS = [('small zip, 01-ZIP-Normal', get_testfile_path('archives', '01-ZIP-Normal.zip')),
         ('big60.cbz, 4.4 MB', os.environ['BIG60'])] + [
    (name, os.path.join(SLOW, name)) for name in sorted(os.listdir(SLOW))]


class Probe(_t._OneBookTest):

    def _block(self, path, rounds=3):
        area = self.dialog.book_area
        backend = self.dialog.backend
        real = backend.get_book_thumbnail
        self.assertTrue(backend.add_book(path) is not None)
        area.display_covers(constants.COLLECTION_ALL)
        pump()
        item = next(i for i in area._covers.each_item() if i.path == path)
        blocks, reads = [], []
        for _ in range(rounds):
            area._covers.stop_update()
            shutil.rmtree(constants.LIBRARY_COVERS_PATH, True)
            area._cache.invalidate_all()
            entered, left = threading.Event(), threading.Event()
            took = []

            def timed(p):
                if p != path:
                    return real(p)
                entered.set()
                t = time.perf_counter()
                try:
                    return real(p)
                finally:
                    took.append(time.perf_counter() - t)
                    left.set()

            area._covers.refresh()
            with unittest.mock.patch.object(backend, 'get_book_thumbnail', timed):
                area._covers.redraw_item(item)
                self.assertTrue(wait_for(entered.is_set, seconds=60))
                t = time.perf_counter()
                area.display_covers(constants.COLLECTION_ALL)
                blocks.append(time.perf_counter() - t)
                self.assertTrue(wait_for(left.is_set, seconds=60))
                area._covers.stop_update()
            reads.append(took[0])
            item = next(i for i in area._covers.each_item() if i.path == path)
        return statistics.median(reads), statistics.median(blocks)

    def test_each(self):
        for name, path in BOOKS:
            read, block = self._block(path, rounds=1 if 'lzma' in name else 3)
            print('PROBE %-34s read %7.0f ms; display_covers blocked %7.0f ms' % (name, read * 1000, block * 1000), flush=True)
