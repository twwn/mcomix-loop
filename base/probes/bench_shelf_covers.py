"""How long the covers of the window's Shelf take to come up.

Run from the checkout, under the gate's Xvfb:

    BOOKS_DIR=<dir kept between runs> env -u WAYLAND_DISPLAY GDK_BACKEND=x11 \
        xvfb-run -d -s "-screen 0 1280x1024x24" timeout -k 5 120 \
        python3 <this file>

BOOKS (400) zips of one 1000x1500 JPEG each are built in BOOKS_DIR once.
Three starts of a MainWindow with no book, each timed from just before
MainWindow() to: display_covers() called, the first cover handed to its
cell, the last cover of a cell in view, the last cover asked for.

  cold   no cover stored: each is read out of its archive
  warm   every cover stored, the in-memory cache emptied: a program start
  warm2  the same again (RUNS times), for the spread

Prints one line per start and, for the warm ones, what one cover cost
on its worker (the mean of _get_pixbuf's wall time) and how many covers
were asked for against how many were in view.
"""
import io
import os
import random
import sys
import threading
import time
import unittest
import zipfile

sys.path.insert(0, os.getcwd())
from PIL import Image, ImageFilter  # noqa: E402
from test import MComixTest, wait_for, pump  # noqa: E402
from mcomix import constants, icons, keybindings, main, thumbnail_list  # noqa: E402
from mcomix.library import backend as library_backend  # noqa: E402
from mcomix.library import book_area  # noqa: E402
from mcomix.library.pixbuf_cache import get_pixbuf_cache  # noqa: E402
from mcomix.preferences import prefs  # noqa: E402

COUNT = int(os.environ.get('BOOKS', '400'))
RUNS = int(os.environ.get('RUNS', '3'))
SIZE = int(os.environ.get('COVER', '125'))
BOOKS_DIR = os.environ['BOOKS_DIR']
DROP = os.environ.get('DROP_CACHE') == '1'
TIMELINE = os.environ.get('TIMELINE') == '1'
PROFILE = os.environ.get('PROFILE') == '1'
#: JUMP=0.5 scrolls to that share of the grid's height once a start has
#: settled, and times the covers there; JUMP_EARLY=1 scrolls as soon as
#: the first covers have been asked for instead, the others in flight.
JUMP = float(os.environ.get('JUMP', '0'))
JUMP_EARLY = os.environ.get('JUMP_EARLY') == '1'
#: SWITCH=3 draws the same collection again that many times once a start
#: has settled, every cover in the memory cache: a collection switch.
SWITCH = int(os.environ.get('SWITCH', '0'))


def build_books():
    os.makedirs(BOOKS_DIR, exist_ok=True)
    paths = [os.path.join(BOOKS_DIR, 'book%05d.cbz' % index)
             for index in range(COUNT)]
    rng = random.Random(7)
    for index, path in enumerate(paths):
        if os.path.exists(path):
            continue
        # Something a photograph compresses like: soft noise over a
        # gradient, so that the JPEG and the stored PNG have real sizes.
        small = Image.frombytes(
            'RGB', (125, 188), rng.randbytes(125 * 188 * 3))
        picture = small.resize((1000, 1500), Image.Resampling.BICUBIC)
        picture = picture.filter(ImageFilter.GaussianBlur(2))
        data = io.BytesIO()
        picture.save(data, 'JPEG', quality=85)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as book:
            book.writestr('p001.jpg', data.getvalue())
            for page in range(2, 21):
                book.writestr('p%03d.jpg' % page, b'')
    return paths


class Probe(MComixTest):

    def _start(self, label):
        """One start of the window; prints its line."""
        calls = []
        finished = {}
        shown = []
        lock = threading.Lock()
        real_get = book_area._BookArea._get_pixbuf
        real_finished = thumbnail_list._ThumbnailViewBase._thumbnail_finished
        real_display = book_area._BookArea.display_covers
        real_ask = thumbnail_list._ThumbnailViewBase._ask_for_unasked
        asks = []
        made = {}

        def ask_for_unasked(view):
            asks.append((time.perf_counter(), len(view._unasked)))
            return real_ask(view)

        thumbnail_list._ThumbnailViewBase._ask_for_unasked = ask_for_unasked

        def get_pixbuf(area, uid):
            begun = time.perf_counter()
            try:
                return real_get(area, uid)
            finally:
                with lock:
                    calls.append(time.perf_counter() - begun)
                    made[uid] = time.perf_counter()

        def thumbnail_finished(view, item, pixbuf, scale=1.0):
            answer = real_finished(view, item, pixbuf, scale)
            finished.setdefault(item, time.perf_counter())
            return answer

        shown_args = []

        def display_covers(area, collection):
            shown.append(time.perf_counter())
            shown_args.append(collection)
            return real_display(area, collection)

        book_area._BookArea._get_pixbuf = get_pixbuf
        thumbnail_list._ThumbnailViewBase._thumbnail_finished = \
            thumbnail_finished
        book_area._BookArea.display_covers = display_covers
        get_pixbuf_cache().invalidate_all()
        if DROP:
            covers = constants.LIBRARY_COVERS_PATH
            if os.path.isdir(covers):
                for name in os.listdir(covers):
                    fd = os.open(os.path.join(covers, name), os.O_RDONLY)
                    os.fsync(fd)
                    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                    os.close(fd)
        profile = None
        if PROFILE and label != 'cold':
            import cProfile
            profile = cProfile.Profile()
            profile.enable()
        begun = time.perf_counter()
        window = main.MainWindow()
        main.set_main_window(window)
        built = time.perf_counter()
        try:
            wait_for(lambda: window._shelf is not None
                     and window._shelf.get_visible(), 20)
            if profile is not None:
                wait_for(lambda: bool(asks), 20)
                profile.disable()
                import pstats
                stats = pstats.Stats(profile, stream=sys.stdout)
                stats.sort_stats('cumulative').print_stats(
                    'mcomix|gi.repository|sqlite|method', 60)
            area = window._shelf.book_area
            covers = area._covers

            def settled():
                bound = [item for item in covers._bound]
                return bool(bound) and not covers._unasked and all(
                    item.thumbnail is not None for item in bound)

            def in_sight():
                height = area.get_height()
                seen = []
                for cell in covers._each_cell():
                    if cell.position < 0:
                        continue
                    found, bounds = cell.compute_bounds(area)
                    if found and cell.get_mapped() \
                            and bounds.get_y() < height \
                            and bounds.get_y() + bounds.get_height() > 0:
                        seen.append(covers.get_item(cell.position))
                return seen

            def jump(name):
                adjustment = area.get_vadjustment()
                with lock:
                    made_before = len(calls)
                done_before = dict(finished)
                finished.clear()
                at = time.perf_counter()
                adjustment.set_value(adjustment.get_upper() * JUMP)
                # Not a predicate that looks at the cells: each call into
                # GTK gives the interpreter lock up, 900 of them a turn
                # with 24 workers after it held every cover back until
                # the workers were done.
                wait_for(settled, 120)
                pump()
                wait_for(settled, 120)
                seen = in_sight()
                times = [finished[item] for item in seen if item in finished]
                first = min(times, default=at)
                seen_at = max(times, default=at)
                stale = [item for item in finished
                         if item not in covers._bound]
                with lock:
                    made_after = len(calls) - made_before
                print('   %-5s to %.0f%%: first in view %4.0f ms | all in view'
                      ' %4.0f | settled %4.0f | in view %d, bound %d | made'
                      ' since %d, of them for cells no longer bound %d'
                      % (name, JUMP * 100, (first - at) * 1000,
                         (seen_at - at) * 1000,
                         (time.perf_counter() - at) * 1000, len(seen),
                         len(covers._bound), made_after, len(stale)),
                      flush=True)
                if TIMELINE:
                    positions = {covers.get_item(i): i
                                 for i in range(covers.model.get_n_items())}
                    sight = sorted(positions[item] for item in seen)
                    print('      adjustment %.0f of %.0f, page %.0f; in view'
                          ' by the cells %d-%d, by the scroll bar %.0f-%.0f'
                          % (adjustment.get_value(), adjustment.get_upper(),
                             adjustment.get_page_size(), sight[0], sight[-1],
                             *covers._positions_on_screen()), flush=True)
                    where = []
                    for cell in covers._each_cell():
                        found, bounds = cell.compute_bounds(area)
                        where.append((cell.position, found and round(
                            bounds.get_y()), cell.get_mapped(),
                            cell.get_parent().get_child_visible()))
                    where.sort()
                    print('      cells (position, y, mapped, child visible):'
                          ' %s' % where[::15], flush=True)
                    def spread(times):
                        times = sorted((t - at) * 1000 for t in times
                                       if t > at)
                        if not times:
                            return 'none'
                        return ' '.join('%.0f' % times[
                            min(len(times) - 1, len(times) * k // 8)]
                            for k in range(9))
                    with lock:
                        print('      made on the workers, ms (eighths): %s'
                              % spread(made.values()), flush=True)
                    print('      handed to the cells, ms (eighths): %s'
                          % spread(finished.values()), flush=True)
                    print('      asks since: %s' % ', '.join(
                        '%d at %.0f' % (count, (asked - at) * 1000)
                        for asked, count in asks if asked > at), flush=True)
                    order = sorted(finished, key=finished.get)
                    print('      handed over (positions): %s' % ' '.join(
                        str(positions.get(item, -1)) for item in order[::8]),
                        flush=True)
                finished.update(done_before)

            if JUMP and JUMP_EARLY:
                wait_for(lambda: bool(asks), 20)
                jump('early')
            # Twice, a frame apart: laying the grid out binds more cells.
            wait_for(settled, 60)
            pump()
            wait_for(settled, 60)
            height = area.get_height()
            in_view = []
            for cell in covers._each_cell():
                if cell.position < 0:
                    continue
                found, bounds = cell.compute_bounds(area)
                if found and bounds.get_y() < height \
                        and bounds.get_y() + bounds.get_height() > 0:
                    in_view.append(covers.get_item(cell.position))
            times = sorted(finished.values())
            view_times = [finished[item] for item in in_view
                          if item in finished]
            print('%-6s window %4.0f ms | covers asked for at %4.0f | '
                  'first cover %4.0f | last in view %4.0f | last asked %4.0f'
                  ' | in view %d, bound %d, made %d | per cover %.2f ms'
                  % (label, (built - begun) * 1000,
                     (shown[0] - begun) * 1000,
                     (times[0] - begun) * 1000,
                     (max(view_times) - begun) * 1000,
                     (times[-1] - begun) * 1000,
                     len(in_view), len(covers._bound), len(calls),
                     sum(calls) / len(calls) * 1000), flush=True)
            if JUMP and not JUMP_EARLY:
                jump('jump')
            if SWITCH:
                # The same collection drawn again, its covers all in the
                # memory cache: what a collection switch back or a
                # search cleared costs.
                clock = area.get_frame_clock()
                painted = []

                def after_paint(frame_clock):
                    if not painted:
                        blank = sum(1 for item in covers._bound
                                    if item.thumbnail is None)
                        painted.append((time.perf_counter(), blank,
                                        len(covers._bound)))

                for turn in range(SWITCH):
                    with lock:
                        made_before = len(calls)
                    painted.clear()
                    handler = clock.connect('after-paint', after_paint)
                    switch_profile = None
                    if PROFILE and turn == 0 and label != 'cold':
                        import cProfile
                        switch_profile = cProfile.Profile()
                        switch_profile.enable()
                    at = time.perf_counter()
                    real_display(area, shown_args[0])
                    returned = time.perf_counter()
                    if switch_profile is not None:
                        switch_profile.disable()
                        import pstats
                        pstats.Stats(switch_profile, stream=sys.stdout
                                     ).sort_stats('tottime').print_stats(25)
                    wait_for(settled, 60)
                    done = time.perf_counter()
                    wait_for(lambda: bool(painted), 5)
                    clock.disconnect(handler)
                    with lock:
                        made_after = len(calls) - made_before
                    paint_at, blank, bound = painted[0] if painted else (
                        at, -1, -1)
                    print('   switch%d: display_covers %5.1f ms | settled'
                          ' %5.1f | first paint %5.1f with %d of %d bound'
                          ' blank | made since %d'
                          % (turn, (returned - at) * 1000,
                             (done - at) * 1000, (paint_at - at) * 1000,
                             blank, bound, made_after), flush=True)
                    pump()
            if TIMELINE:
                print('   asks: %s' % ', '.join(
                    '%d at %.0f' % (count, (at - begun) * 1000)
                    for at, count in asks), flush=True)
                view = sorted((finished[item], made.get(item.uid, 0),
                               item.uid) for item in in_view
                              if item in finished)
                print('   in view, made/handed over (ms): %s' % ' '.join(
                    '%.0f/%.0f' % ((m - begun) * 1000, (f - begun) * 1000)
                    for f, m, uid in view[::6]), flush=True)
                positions = {covers.get_item(i): i
                             for i in range(covers.model.get_n_items())}
                order = sorted(finished, key=finished.get)
                print('   order handed over (positions): %s' % ' '.join(
                    str(positions.get(item, -1)) for item in order[:120]),
                    flush=True)
        finally:
            book_area._BookArea._get_pixbuf = real_get
            thumbnail_list._ThumbnailViewBase._thumbnail_finished = \
                real_finished
            book_area._BookArea.display_covers = real_display
            thumbnail_list._ThumbnailViewBase._ask_for_unasked = real_ask
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump()

    def test_starts(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        keybindings._manager = None
        prefs['library cover size'] = SIZE
        prefs['window width'] = 1200
        prefs['window height'] = 900
        if os.environ.get('THREADS'):
            # The cover pool reads it when the cover area is built.
            prefs['max threads'] = int(os.environ['THREADS'])
        paths = build_books()
        backend = library_backend.LibraryBackend()
        begun = time.perf_counter()
        with backend.transaction():
            for path in paths:
                backend.add_book(path)
        print('%d books added in %.0f ms; cover size %d; threads %s'
              % (len(paths), (time.perf_counter() - begun) * 1000, SIZE,
                 prefs['max threads']), flush=True)
        self._start('cold')
        stored = os.listdir(constants.LIBRARY_COVERS_PATH)
        print('stored covers: %d, %.1f kB each' % (
            len(stored), sum(os.path.getsize(os.path.join(
                constants.LIBRARY_COVERS_PATH, name)) for name in stored)
            / max(1, len(stored)) / 1000), flush=True)
        for run in range(RUNS):
            self._start('warm%d' % run)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], 'Probe'], exit=False)
    sys.stdout.flush()
    # os._exit skips atexit: test/tmp/session.* and its pymp-* stayed.
    import atexit
    atexit._run_exitfuncs()
    os._exit(0)
