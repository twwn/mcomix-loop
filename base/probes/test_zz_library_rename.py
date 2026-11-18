"""Probe: "Rename" from the library's covers, in a real library window,
for a book not open and for the one being read.  Copy under test/ as
test_zz_library_rename.py, run alone under xvfb-run, remove after."""
import os, shutil, time, unittest.mock
from gi.repository import Gtk
from . import MComixTest, get_testfile_path, pump, wait_for
from mcomix import constants, icons, main, rename_dialog
from mcomix.dialog import Response
from mcomix.library import main_dialog


class Probe(MComixTest):
    def test_rename(self):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        books = []
        for name in ('Aaa.cbz', 'Bbb.cbz'):
            path = os.path.join(self.tmp_dir, name)
            shutil.copy(get_testfile_path('archives', '01-ZIP-Normal.zip'), path)
            books.append(path)
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

            def rename(path, typed):
                covers.selection.unselect_all()
                for pos, item in enumerate(covers.each_item()):
                    if item.path == path:
                        covers.selection.select_item(pos, True)
                parents = []
                def ask(parent, *, title, prompt, name, clash, answered):
                    parents.append(type(parent).__name__)
                    answered(Response.OK, typed)
                with unittest.mock.patch.object(rename_dialog, 'ask', ask):
                    lib.book_area.rename_selected()
                for _ in range(60): pump(); time.sleep(0.02)
                return parents

            p = rename(books[1], 'Zzz')
            print('PROBE not open: asked over', p, 'items', sorted(os.path.basename(i.path) for i in covers.each_item()),
                  'files', sorted(os.listdir(self.tmp_dir)), 'in library', lib.backend.get_book_by_path(os.path.join(self.tmp_dir, 'Zzz.cbz')) is not None)
            p = rename(books[0], 'Open renamed')
            wait_for(lambda: window.imagehandler.get_number_of_pages() > 0, seconds=20)
            for _ in range(30): pump(); time.sleep(0.02)
            print('PROBE open: asked over', p, 'items', sorted(os.path.basename(i.path) for i in covers.each_item()),
                  'window reads', os.path.basename(window.filehandler.get_path_to_base() or ''), 'page', window.imagehandler.get_current_page())
        finally:
            main_dialog._close_dialog()
            for w in Gtk.Window.list_toplevels():
                if w is not window and w.get_visible(): w.destroy()
            window.terminate_program(); window.destroy(); main.set_main_window(None); pump()
