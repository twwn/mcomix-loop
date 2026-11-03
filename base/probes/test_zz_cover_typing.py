"""Typing 8 letters over a slow cover not yet stored: reads started, main-thread stalls."""
import os, shutil, threading, time, unittest.mock
from test import pump, wait_for
from test import test_library_dialog as _t
from mcomix import constants

PATH = os.path.join(os.environ['SLOW_DIR'], 'solid-lzma-400MB-cover-last.7z')


class Probe(_t._OneBookTest):

    def test_typing(self):
        area, backend = self.dialog.book_area, self.dialog.backend
        real = backend.get_book_thumbnail
        backend.add_book(PATH)
        area.display_covers(constants.COLLECTION_ALL)
        pump()
        self.assertTrue(wait_for(lambda: all(i.thumbnail is not None for i in area._covers.each_item()), seconds=30))
        area._covers.stop_update()
        shutil.rmtree(constants.LIBRARY_COVERS_PATH, True)
        area._cache.invalidate_all()
        lock = threading.Lock()
        running = [0]; peak = [0]; reads = [0]

        def counted(p):
            if p != PATH:
                return real(p)
            with lock:
                reads[0] += 1; running[0] += 1; peak[0] = max(peak[0], running[0])
            try:
                return real(p)
            finally:
                with lock:
                    running[0] -= 1

        with unittest.mock.patch.object(backend, 'get_book_thumbnail', counted):
            start = time.perf_counter()
            stalls = []
            for letter in range(8):
                t = time.perf_counter()
                area.display_covers(constants.COLLECTION_ALL)
                stalls.append(time.perf_counter() - t)
                until = time.perf_counter() + 0.2
                while time.perf_counter() < until:
                    pump()
            shown = wait_for(lambda: all(i.thumbnail is not None for i in area._covers.each_item()), seconds=60)
            took = time.perf_counter() - start
            self.assertTrue(shown)
            wait_for(lambda: running[0] == 0, seconds=60)
            area._covers.stop_update()
        print('PROBE 8 letters: worst stall %.0f ms, total stall %.0f ms; reads of the book %d, %d at once; cover shown after %.1f s; pool %d' % (
            max(stalls) * 1000, sum(stalls) * 1000, reads[0], peak[0], took, area._covers._thread._max_threads), flush=True)

    def test_closing(self):
        """What is left of the join: stop_update() from the library's close()."""
        area, backend = self.dialog.book_area, self.dialog.backend
        real = backend.get_book_thumbnail
        backend.add_book(PATH)
        area.display_covers(constants.COLLECTION_ALL)
        pump()
        self.assertTrue(wait_for(lambda: all(i.thumbnail is not None for i in area._covers.each_item()), seconds=30))
        area._covers.stop_update()
        shutil.rmtree(constants.LIBRARY_COVERS_PATH, True)
        area._cache.invalidate_all()
        entered = threading.Event()

        def timed(p):
            if p == PATH:
                entered.set()
            return real(p)

        with unittest.mock.patch.object(backend, 'get_book_thumbnail', timed):
            area.display_covers(constants.COLLECTION_ALL)
            self.assertTrue(wait_for(entered.is_set, seconds=30))
            t = time.perf_counter()
            area.stop_update()
            print('PROBE stop_update(), as the library window closes: %.0f ms' % ((time.perf_counter() - t) * 1000), flush=True)
