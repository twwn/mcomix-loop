"""Probe: a real ALT+Return on the library's covers opens the book
properties, and not the main window's.  Copy under test/ as
test_zz_library_alt_return.py, run alone under xvfb-run, remove after."""
import os, subprocess, time
from gi.repository import Gtk
from . import MComixTest, get_testfile_path, pump, wait_for
from mcomix import constants, icons, main, properties_dialog
from mcomix.library import book_properties, main_dialog


def shown(kind):
    return [w for w in Gtk.Window.list_toplevels()
            if isinstance(w, kind) and w.get_visible()]


class Probe(MComixTest):
    def test_alt_return(self):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow(open_path=get_testfile_path('archives', '01-ZIP-Normal.zip'))
        main.set_main_window(window)
        window.set_title('probewin')
        window.present()
        for _ in range(30): pump(); time.sleep(0.02)
        try:
            main_dialog.open_dialog(None, window)
            lib = main_dialog._dialog
            lib.set_title('probelib')
            lib.backend.add_book(get_testfile_path('archives', '01-ZIP-Normal.zip'))
            lib.book_area.display_covers(constants.COLLECTION_ALL)
            covers = lib.book_area._covers
            wait_for(lambda: any(covers.each_item()), seconds=10)
            for _ in range(50): pump(); time.sleep(0.02)
            covers.select_and_focus(0)
            child = covers.get_first_child()
            while child is not None and not child.get_focusable():
                child = child.get_next_sibling()
            print('PROBE grab', type(child).__name__ if child else None, child.grab_focus() if child else None)
            for _ in range(20): pump(); time.sleep(0.02)
            root = lib.book_area.get_root()
            print('PROBE root', type(root).__name__, 'focus', type(root.get_focus()).__name__)
            xid = root.get_surface().get_xid()
            subprocess.run(['xdotool', 'windowfocus', '--sync', str(xid)])
            for _ in range(10): pump(); time.sleep(0.02)
            seen = []
            spy = Gtk.EventControllerKey()
            spy.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
            spy.connect('key-pressed', lambda c, k, code, st: (seen.append(('root', k, int(st))), False)[1])
            root.add_controller(spy)
            lib.book_area._copy_selected = lambda *a: seen.append('copy')
            subprocess.run(['xdotool', 'key', 'ctrl+c'], check=True)
            for _ in range(20): pump(); time.sleep(0.02)
            print('PROBE ctrl+c reached:', seen)
            subprocess.run(['xdotool', 'key', 'alt+Return'], check=True)
            for _ in range(50): pump(); time.sleep(0.02)
            print('PROBE book properties=%d window properties=%d' % (
                len(shown(book_properties.BookPropertiesDialog)),
                len(shown(properties_dialog._PropertiesDialog))))
        finally:
            for kind in (book_properties.BookPropertiesDialog, properties_dialog._PropertiesDialog):
                for w in shown(kind): w.destroy()
            main_dialog._close_dialog()
            for w in Gtk.Window.list_toplevels():
                if isinstance(w, main_dialog._LibraryDialog): w.destroy()
            window.terminate_program(); window.destroy(); main.set_main_window(None); pump()
