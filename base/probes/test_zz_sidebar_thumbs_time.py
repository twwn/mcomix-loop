"""Probe: how long the sidebar takes to show the thumbnails of the pages
in view of a book of 60 large JPEG pages (big60.cbz, beside this file),
from the window being built; prints when the first and the last
thumbnail made came, how many, their mean wall time on a worker, the
most times one page was made, and how often the sidebar was resized,
cleared or loaded and the view's items set, redrawn or invalidated.
Also: rows left blank, the pool's state and the workers' stacks if any
are, and the calls answered None (page not out of the archive yet).
THREADS sets "max threads" (0, the default, one per processor).
Copy into test/ and run with pytest -s under xvfb-run."""
import collections
import os
import shutil
import time
import traceback

from . import MComixTest, pump, wait_for

from mcomix import constants, icons, main, thumbbar, thumbnail_list
from mcomix.preferences import prefs

BOOK = os.path.join(os.path.expanduser('~'), '.claude', 'skills', 'mcomix-loop',
                    'state', 'probes', 'big60.cbz')
WATCHED = ((thumbbar.ThumbnailSidebar, 'resize'),
           (thumbbar.ThumbnailSidebar, 'clear'),
           (thumbbar.ThumbnailSidebar, 'load_thumbnails'),
           (thumbnail_list._ThumbnailViewBase, 'set_items'),
           (thumbnail_list._ThumbnailViewBase, 'redraw_item'),
           (thumbnail_list._ThumbnailViewBase, 'invalidate_all'))


class SidebarThumbsProbe(MComixTest):

    def test_probe(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        book = os.path.join(self.tmp_dir, 'big60.cbz')
        shutil.copy(BOOK, book)
        prefs['show thumbnails'] = True
        prefs['max threads'] = int(os.environ.get('THREADS', '0'))
        icons.load_icons()
        made = []
        events = []
        stacks = collections.Counter()
        original = thumbbar.ThumbnailSidebar._generate_thumbnail

        def timed(sidebar, uid):
            begun = time.perf_counter()
            pixbuf = original(sidebar, uid)
            made.append((time.perf_counter(), time.perf_counter() - begun, uid,
                         pixbuf is not None))
            return pixbuf
        thumbbar.ThumbnailSidebar._generate_thumbnail = timed
        self.addCleanup(setattr, thumbbar.ThumbnailSidebar,
                        '_generate_thumbnail', original)
        for owner, name in WATCHED:
            if not hasattr(owner, name):
                continue
            old = getattr(owner, name)

            def wrap(self_, *args, _old=old, _name=name, **kwargs):
                events.append((time.perf_counter(), _name))
                if os.environ.get('STACKS') == _name:
                    stacks[''.join(traceback.format_stack(limit=6)[:-1])] += 1
                return _old(self_, *args, **kwargs)
            setattr(owner, name, wrap)
            self.addCleanup(setattr, owner, name, old)
        for run in range(3):
            made.clear()
            events.clear()
            begun = time.perf_counter()
            window = main.MainWindow(open_path=book)
            main.set_main_window(window)
            window.set_default_size(1200, 900)
            window.present()
            self.assertTrue(wait_for(
                lambda: window.imagehandler.get_number_of_pages() == 60,
                seconds=30))
            sidebar = window.thumbnailsidebar
            wait_for(lambda: len(made) >= 1, seconds=30)
            # pump(n) returns at once when nothing is pending, so it is no
            # measure of time: wait on time for every row, then 300 ms more
            # for whatever is still asked.
            wait_for(lambda: window.imagehandler.page_is_available(60)
                     and not any(item.thumbnail is None
                                 for item in sidebar._list._bound),
                     seconds=20)
            wait_for(lambda: False, seconds=0.3)
            blank = sorted(item.uid for item in sidebar._list._bound
                           if item.thumbnail is None)
            print('PROBE   bound rows still blank: %d %s;'
                  ' pages out %d' % (len(blank), blank[:8], sum(
                      1 for page in range(1, 61)
                      if window.imagehandler.page_is_available(page))),
                  flush=True)
            pool = sidebar._list._thread
            print('PROBE   pool: queue %d (blank in it %d), in hand %s, at once %s,'
                  ' threads %d alive %d, uids held %d' % (
                      len(pool._orders_queue),
                      sum(1 for item in pool._orders_queue
                          if item.uid in blank),
                      getattr(pool, '_in_hand', '-'),
                      getattr(pool, '_at_once', '-'), len(pool._threads),
                      sum(1 for t in pool._threads if t.is_alive()),
                      len(pool._orders_set)), flush=True)
            if blank:
                import sys
                frames = sys._current_frames()
                where = collections.Counter()
                for thread in pool._threads:
                    frame = frames.get(thread.ident)
                    if frame is not None:
                        where[''.join(traceback.format_stack(frame)[-4:])] += 1
                for stack, times in where.most_common(4):
                    print('PROBE   worker stack x%d:\n%s' % (times, stack),
                          flush=True)
            if blank:
                waited = time.perf_counter()
                done = wait_for(lambda: not any(
                    item.thumbnail is None for item in sidebar._list._bound),
                    seconds=20)
                recent = [m for m in made if m[0] >= waited]
                print('PROBE   filled: %s after %.0f ms more; %d made meanwhile,'
                      ' mean %.1f ms on a worker; at once now %s' % (
                          done, (time.perf_counter() - waited) * 1000,
                          len(recent), sum(m[1] for m in recent)
                          / max(len(recent), 1) * 1000,
                          getattr(pool, '_at_once', '-')), flush=True)
            per = collections.Counter(m[2] for m in made if m[3])
            print('PROBE   calls answered None (page not out yet): %d' % sum(
                1 for m in made if not m[3]), flush=True)
            print('PROBE run %d: %d made; first at %.0f ms, last at %.0f ms;'
                  ' mean on a worker %.1f ms; bound %d' % (
                      run, len(made), (made[0][0] - begun) * 1000,
                      (made[-1][0] - begun) * 1000,
                      sum(m[1] for m in made) / len(made) * 1000,
                      len(sidebar._list._bound)), flush=True)
            print('PROBE   made per page: max %d over %d pages, %d in all; events %s' % (
                max(per.values()), len(per), sum(per.values()),
                collections.Counter(n for _, n in events).most_common()),
                flush=True)
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump(1000)
        for stack, times in stacks.most_common(3):
            print('PROBE stack x%d:\n%s' % (times, stack), flush=True)
