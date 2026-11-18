"""Probe: does a ThumbnailGridView build its cells anew when set_items()
replaces every entry?  Counts _setup_cell and _unbind_cell calls and
times set_items() up to the next drawn frame for three cases:

  new    the same uids, new ThumbnailItem objects (display_covers today)
  same   the very objects shown before
  half   half of them the same objects, half new
"""
import time

from gi.repository import GdkPixbuf, Gtk

from test import MComixTest, pump, wait_for

from mcomix import thumbnail_list

ITEMS = 400


class GridSpliceProbe(MComixTest):

    def test_probe(self):
        counts = {'setup': 0, 'unbind': 0, 'teardown': 0}
        setup = thumbnail_list._ThumbnailViewBase._setup_cell
        unbind = thumbnail_list._ThumbnailViewBase._unbind_cell

        def counting_setup(view, factory, list_item):
            counts['setup'] += 1
            return setup(view, factory, list_item)

        def counting_unbind(view, factory, list_item):
            counts['unbind'] += 1
            return unbind(view, factory, list_item)
        thumbnail_list._ThumbnailViewBase._setup_cell = counting_setup
        thumbnail_list._ThumbnailViewBase._unbind_cell = counting_unbind
        self.addCleanup(setattr, thumbnail_list._ThumbnailViewBase,
                        '_setup_cell', setup)
        self.addCleanup(setattr, thumbnail_list._ThumbnailViewBase,
                        '_unbind_cell', unbind)

        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 125, 180)
        pixbuf.fill(0x808080ff)
        view = thumbnail_list.ThumbnailGridView()
        view.generate_thumbnail = lambda uid: pixbuf
        view.thumbnail_at_hand = lambda item: pixbuf
        view.set_thumbnail_size(125)
        scroller = Gtk.ScrolledWindow()
        scroller.set_child(view)
        window = Gtk.Window()
        window.set_default_size(1200, 900)
        window.set_child(scroller)
        window.present()
        self.addCleanup(window.destroy)
        self.addCleanup(view.stop_update)
        items = [thumbnail_list.ThumbnailItem(uid) for uid in range(ITEMS)]
        view.set_items(items)
        wait_for(lambda: False, seconds=1)
        clock = window.get_frame_clock()

        for case in ('new', 'same', 'half', 'new', 'same'):
            if case == 'new':
                fresh = [thumbnail_list.ThumbnailItem(uid) for uid in range(ITEMS)]
            elif case == 'same':
                fresh = list(items)
            else:
                fresh = [items[uid] if uid % 2 else thumbnail_list.ThumbnailItem(uid)
                         for uid in range(ITEMS)]
            for key in counts:
                counts[key] = 0
            frame = clock.get_frame_counter()
            start = time.perf_counter()
            view.set_items(fresh)
            spliced = time.perf_counter() - start
            wait_for(lambda: clock.get_frame_counter() > frame + 1)
            drawn = time.perf_counter() - start
            print('PROBE %-4s setup %3d unbind %3d  set_items %.1f ms, two frames %.1f ms'
                  % (case, counts['setup'], counts['unbind'], spliced * 1000, drawn * 1000))
            items = fresh
            wait_for(lambda: False, seconds=0.3)
