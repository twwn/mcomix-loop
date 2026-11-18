"""Probe: the Properties opened from the shelf (the library's covers in
the main window while no book is open), by show_properties() or by a
real key (PROBE_KEY, e.g. alt+Return): which window opens, rendered to
PROBE_OUT.  PROBE_PATH names the book.  Copy under test/ as
test_zz_shelf_props_cover.py, run alone under xvfb-run, remove after."""
import os, subprocess, time
from gi.repository import Gtk
from . import MComixTest, pump, wait_for
from mcomix import constants, icons, main
from mcomix.library import backend
from mcomix.preferences import prefs


def render(widget, out):
    paintable = Gtk.WidgetPaintable.new(widget)
    snapshot = Gtk.Snapshot()
    paintable.snapshot(snapshot, widget.get_width(), widget.get_height())
    widget.get_renderer().render_texture(snapshot.to_node(), None).save_to_png(out)


class Probe(MComixTest):
    def test_cover(self):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        book = os.environ['PROBE_PATH']
        backend.LibraryBackend().add_book(book)
        if os.environ.get('PROBE_MORE'):
            import glob
            for other in sorted(glob.glob(os.path.join(os.environ['PROBE_MORE'], '*.cbz'))):
                backend.LibraryBackend().add_book(other)
        prefs['show library without book'] = True
        if os.environ.get('PROBE_COVER_SIZE'):
            prefs['library cover size'] = int(os.environ['PROBE_COVER_SIZE'])
        window = main.MainWindow()
        main.set_main_window(window)
        window.set_title('probewin')
        window.present()
        for _ in range(30): pump(); time.sleep(0.02)
        try:
            window.update_shelf()
            area = window._shelf.book_area
            covers = area._covers
            wait_for(lambda: any(i.thumbnail is not None for i in covers.each_item()), seconds=10)
            for _ in range(30): pump(); time.sleep(0.02)
            covers.selection.select_item(int(os.environ.get("PROBE_ITEM", "0")), True) if os.environ.get("PROBE_MORE") else covers.selection.select_all()
            if os.environ.get('PROBE_ACTION'):
                action = window.actiongroup.get_action('properties')
                print('PROBE window properties sensitive', action.get_sensitive())
                action.activate()
                for _ in range(20): pump(); time.sleep(0.02)
            elif os.environ.get('PROBE_KEY'):
                child = covers.get_first_child()
                while child is not None and not child.get_focusable():
                    child = child.get_next_sibling()
                if not os.environ.get('PROBE_NOFOCUS'):
                    child.grab_focus()
                for _ in range(10): pump(); time.sleep(0.02)
                xid = window.get_surface().get_xid()
                subprocess.run(['xdotool', 'windowfocus', '--sync', str(xid)])
                for _ in range(10): pump(); time.sleep(0.02)
                print('PROBE focus', type(window.get_focus()).__name__)
                subprocess.run(['xdotool', 'key', os.environ['PROBE_KEY']], check=True)
                for _ in range(50): pump(); time.sleep(0.02)
            elif os.environ.get('PROBE_LIBRARY'):
                from mcomix.library import main_dialog
                main_dialog.open_dialog(None, window)
                lib = main_dialog._dialog
                for _ in range(30): pump(); time.sleep(0.02)
                lib.book_area.display_covers(constants.COLLECTION_ALL)
                lc = lib.book_area._covers
                wait_for(lambda: any(i.thumbnail is not None for i in lc.each_item()), seconds=10)
                for _ in range(30): pump(); time.sleep(0.02)
                lc.selection.select_all()
                cached = lib.book_area._cache.get(os.path.abspath(book))
                print('PROBE cached', cached and (cached.get_width(), cached.get_height(), cached.get_has_alpha()))
                lib.book_area.show_properties()
                for _ in range(20): pump(); time.sleep(0.02)
            else:
                area.show_properties()
                for _ in range(20): pump(); time.sleep(0.02)
            dialogs = [w for w in Gtk.Window.list_toplevels()
                       if w is not window and w.get_visible() and type(w).__name__ == 'BookPropertiesDialog']
            print('PROBE opened', [type(w).__name__ for w in dialogs], type(window.get_renderer()).__name__)
            out = os.environ['PROBE_OUT']
            if dialogs:
                paintable = dialogs[0].page._thumb.get_paintable()
                texture = getattr(paintable, 'texture', paintable)
                if texture is not None:
                    texture.save_to_png(out + '.texture.png')
                print('PROBE paintable', type(paintable).__name__,
                      texture and (texture.get_width(), texture.get_height()),
                      'scale', window.get_scale_factor(), area._covers.device_scale,
                      'cached', (lambda c: c and (c.get_width(), c.get_height()))(area._cache.get(os.path.abspath(book))))
                render(dialogs[0], out)
            render(window, out + '.window.png')
            print('PROBE saved', out)
        finally:
            for w in Gtk.Window.list_toplevels():
                if w is not window and w.get_visible(): w.destroy()
            window.terminate_program(); window.destroy(); main.set_main_window(None); pump()
