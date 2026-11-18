"""Probe: the cover the library's Properties show, in a real library
window: what the cache holds and what the dialog draws.  Copy under
test/ as test_zz_library_props_cover.py, run alone under xvfb-run,
remove after."""
import os, time
from gi.repository import Gtk
from . import MComixTest, get_testfile_path, pump, wait_for
from mcomix import constants, icons, main
from mcomix.library import book_properties, main_dialog


def stats(pixbuf):
    px = pixbuf.get_pixels(); n = pixbuf.get_n_channels(); rs = pixbuf.get_rowstride()
    w, h = pixbuf.get_width(), pixbuf.get_height()
    samples = [tuple(px[y * rs + x * n: y * rs + x * n + n]) for x, y in ((w // 2, h // 2), (2, 2), (w // 4, h // 3))]
    return '%dx%d alpha=%s samples=%s' % (w, h, pixbuf.get_has_alpha(), samples)


class Probe(MComixTest):
    def test_cover(self):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        book = os.environ.get('PROBE_PATH') or get_testfile_path('archives', os.environ.get('PROBE_BOOK', '01-ZIP-Normal.zip'))
        window = main.MainWindow()
        main.set_main_window(window)
        for _ in range(20): pump(); time.sleep(0.02)
        try:
            main_dialog.open_dialog(None, window)
            lib = main_dialog._dialog
            lib.add_books([book])
            lib.book_area.display_covers(constants.COLLECTION_ALL)
            covers = lib.book_area._covers
            wait_for(lambda: any(i.thumbnail is not None for i in covers.each_item()), seconds=10)
            for _ in range(30): pump(); time.sleep(0.02)
            cached = lib.book_area._cache.get(os.path.abspath(book))
            print('PROBE cached', None if cached is None else stats(cached))
            covers.selection.select_all()
            if os.environ.get('PROBE_EVICT'):
                lib.book_area._cache.invalidate_all()
            lib.book_area.show_properties()
            for _ in range(20): pump(); time.sleep(0.02)
            dialog = [w for w in Gtk.Window.list_toplevels() if isinstance(w, book_properties.BookPropertiesDialog)][0]
            texture = dialog.page._thumb.get_paintable()
            print('PROBE paintable', type(texture).__name__)
            if texture is None:
                class T:
                    def save_to_png(self, p): pass
                texture = T()
            from mcomix import image_tools
            if hasattr(texture, 'download'):
                pass
            out = os.environ.get('PROBE_OUT', '/tmp/probe_props.png')
            getattr(texture, 'save_to_png', print)(out + '.texture.png')
            paintable = Gtk.WidgetPaintable.new(dialog)
            snapshot = Gtk.Snapshot()
            paintable.snapshot(snapshot, dialog.get_width(), dialog.get_height())
            node = snapshot.to_node()
            dialog.get_renderer().render_texture(node, None).save_to_png(out)
            print('PROBE saved', out)
            print('PROBE thumb size', dialog.page._thumb.get_width(), dialog.page._thumb.get_height())
        finally:
            main_dialog._close_dialog()
            for w in Gtk.Window.list_toplevels():
                if w is not window and w.get_visible(): w.destroy()
            window.terminate_program(); window.destroy(); main.set_main_window(None); pump()
