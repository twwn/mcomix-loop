"""Probe: "Move to" from the library's covers, in a real library window:
the covers' own moveto actions are found, not the window's, the open
book is reopened where it landed.  Copy under test/ as
test_zz_library_move.py, run alone under xvfb-run, remove after."""
import os, shutil, time
from gi.repository import GLib, Gtk
from . import MComixTest, get_testfile_path, pump, wait_for
from mcomix import constants, icons, main
from mcomix.library import main_dialog


class Probe(MComixTest):
    def test_move(self):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        books = []
        for name in ('Aaa.cbz', 'Bbb.cbz'):
            path = os.path.join(self.tmp_dir, name)
            shutil.copy(get_testfile_path('archives', '01-ZIP-Normal.zip'), path)
            books.append(path)
        dest = os.path.join(self.tmp_dir, 'dest')
        os.makedirs(dest)
        window = main.MainWindow(open_path=books[0])
        main.set_main_window(window)
        wait_for(lambda: window.imagehandler.get_number_of_pages() > 0, seconds=20)
        window.set_page(3)
        for _ in range(30): pump(); time.sleep(0.02)
        try:
            main_dialog.open_dialog(None, window)
            lib = main_dialog._dialog
            lib.add_books(books)
            lib.book_area.display_covers(constants.COLLECTION_ALL)
            covers = lib.book_area._covers
            wait_for(lambda: len(list(covers.each_item())) == 2, seconds=10)
            for _ in range(30): pump(); time.sleep(0.02)
            covers.selection.select_all()
            area = lib.book_area
            area._popup_book_menu()
            for _ in range(10): pump(); time.sleep(0.02)
            area._book_menu.popdown()
            print('PROBE submenu entries', area._move_to.model.get_n_items())
            ok = area.activate_action('moveto.move', GLib.Variant.new_bytestring(os.fsencode(dest)))
            for _ in range(80): pump(); time.sleep(0.02)
            wait_for(lambda: window.imagehandler.get_number_of_pages() > 0, seconds=20)
            for _ in range(20): pump(); time.sleep(0.02)
            print('PROBE activated', ok, 'dest', sorted(os.listdir(dest)), 'items',
                  sorted(os.path.relpath(i.path, self.tmp_dir) for i in covers.each_item()),
                  'window reads', os.path.relpath(window.filehandler.get_path_to_base(), self.tmp_dir),
                  'page', window.imagehandler.get_current_page(),
                  'remembered', [os.path.relpath(p, self.tmp_dir) for p in __import__('mcomix.preferences', fromlist=['prefs']).prefs['recent move destinations']])
            window.file_actions.move_current_file(self.tmp_dir)
            for _ in range(80): pump(); time.sleep(0.02)
            print('PROBE window moved its book back; library items',
                  sorted(os.path.relpath(i.path, self._tmp if hasattr(self, '_tmp') else self.tmp_dir) for i in covers.each_item()))
        finally:
            main_dialog._close_dialog()
            for w in Gtk.Window.list_toplevels():
                if w is not window and w.get_visible(): w.destroy()
            window.terminate_program(); window.destroy(); main.set_main_window(None); pump()
