"""Screenshot of the main window for docs/images.

Run from the checkout:
  timeout -k 5 60 env -u WAYLAND_DISPLAY GDK_BACKEND=x11 LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE=en \
    xvfb-run -a -s '-screen 0 1920x1080x24' python3 <this> <outdir>
Opens test/files/pepper-and-carrot at pages 2-3 in double page mode, at
1280x800, and writes <outdir>/mcomix-mainwindow.png; then fills a
library with four books cut from the same archive, each starting on
another page, and writes <outdir>/mcomix-library.png at 800x540;
Probe.test_continuous writes <outdir>/mcomix-continuous.png, pages 2-3
as one strip at 60 per cent width.  All
are full colour: run pngquant --speed 1 on them before committing.
Add a test name (Probe.test_library) after <outdir> to take one alone.
"""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.getcwd())
OUT = sys.argv.pop(1)
ONLY = sys.argv[1:]

from gi.repository import Gtk  # noqa: E402

from test import MComixTest, wait_for, pump  # noqa: E402
from mcomix import constants, icons, keybindings, main, theme  # noqa: E402
from mcomix.preferences import prefs  # noqa: E402

BOOK = os.path.join(os.getcwd(), 'test', 'files', 'pepper-and-carrot',
                    'Pepper-and-Carrot_E01_The-Potion-of-Flight.cbz')


class Probe(MComixTest):

    def test_main_window(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        prefs['show toolbar'] = True
        prefs['show menubar'] = True
        prefs['show statusbar'] = True
        prefs['show thumbnails'] = True
        prefs['default double page'] = True
        prefs['window width'] = 1280
        prefs['window height'] = 800
        prefs['colour scheme'] = theme.LIGHT
        theme.follow_theme()
        icons.load_icons()
        keybindings._manager = None
        window = main.MainWindow(open_path=BOOK)
        main.set_main_window(window)
        try:
            window.set_decorated(False)
            window.set_default_size(1280, 800)
            window.present()
            pump(2000)
            window.set_page(2)
            pump(2000)
            wait_for(lambda: False, seconds=3)
            pump(2000)
            print('size', window.get_width(), window.get_height(), flush=True)
            raw = os.path.join(OUT, 'raw.png')
            subprocess.run(['import', '-window', 'root', raw], check=True)
            subprocess.run(['magick', raw, '-crop', '1280x800+0+0', '+repage',
                            os.path.join(OUT, 'mcomix-mainwindow.png')],
                           check=True)
            os.remove(raw)
        finally:
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump(2000)


    def test_continuous(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        prefs['show toolbar'] = True
        prefs['show menubar'] = True
        prefs['show statusbar'] = True
        prefs['show thumbnails'] = True
        prefs['default double page'] = False
        prefs['continuous mode'] = True
        prefs['continuous width'] = 60
        prefs['window width'] = 1280
        prefs['window height'] = 800
        prefs['colour scheme'] = theme.LIGHT
        theme.follow_theme()
        icons.load_icons()
        keybindings._manager = None
        window = main.MainWindow(open_path=BOOK)
        main.set_main_window(window)
        try:
            window.set_decorated(False)
            window.set_default_size(1280, 800)
            window.present()
            pump(2000)
            window.set_page(2)
            pump(2000)
            wait_for(lambda: False, seconds=2)
            window.scroll(0, 800)
            pump(2000)
            wait_for(lambda: False, seconds=3)
            pump(2000)
            print('size', window.get_width(), window.get_height(), flush=True)
            raw = os.path.join(OUT, 'raw.png')
            subprocess.run(['import', '-window', 'root', raw], check=True)
            subprocess.run(['magick', raw, '-crop', '1280x800+0+0', '+repage',
                            os.path.join(OUT, 'mcomix-continuous.png')],
                           check=True)
            os.remove(raw)
        finally:
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump(2000)

    def test_library(self):
        import zipfile
        from mcomix import constants as consts
        from mcomix.library import main_dialog
        for directory in (consts.CONFIG_DIR, consts.DATA_DIR,
                          consts.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        prefs['colour scheme'] = theme.LIGHT
        prefs['lib window width'] = 800
        prefs['lib window height'] = 540
        prefs['library cover size'] = 150
        prefs['last library collection'] = consts.COLLECTION_ALL
        theme.follow_theme()
        icons.load_icons()
        keybindings._manager = None
        with zipfile.ZipFile(BOOK) as source:
            pages = sorted(name for name in source.namelist()
                           if name.endswith('.jpg'))
            books = []
            for start in range(len(pages)):
                path = os.path.join(self.tmp_dir,
                                    'Pepper-and-Carrot_E01_%d.cbz' % (start + 1))
                with zipfile.ZipFile(path, 'w') as book:
                    for name in pages[start:]:
                        book.writestr(name, source.read(name))
                books.append(path)
        window = main.MainWindow()
        main.set_main_window(window)
        pump(2000)
        try:
            main_dialog.open_dialog(None, window)
            pump(2000)
            dialog = main_dialog._dialog
            dialog.set_decorated(False)
            backend = dialog.backend
            for name in ('Manga', 'Western', 'Pepper&Carrot'):
                backend.add_collection(name)
            pepper = backend.get_collection_by_name('Pepper&Carrot').id
            for path in books:
                backend.add_book(path, pepper)
            dialog.collection_area.display_collections()
            area = dialog.book_area
            area.display_covers(consts.COLLECTION_ALL)
            covers = area._covers
            wait_for(lambda: covers.model.get_n_items() == len(books), 10)
            wait_for(lambda: all(item.thumbnail is not None
                                 for item in covers.each_item()), 20)
            covers.select_positions([1])
            area._mark_books(True)
            pump(2000)
            covers.select_positions([])
            pump(2000)
            wait_for(lambda: all(item.thumbnail is not None
                                 for item in covers.each_item()), 20)
            dialog.present()
            # Off the window, or a tooltip stands in the shot.
            subprocess.run(['xdotool', 'mousemove', '1900', '1060'])
            wait_for(lambda: False, seconds=2)
            print('library', dialog.get_width(), dialog.get_height(),
                  [item.thumbnail is not None for item in covers.each_item()],
                  flush=True)
            raw = os.path.join(OUT, 'raw.png')
            subprocess.run(['import', '-window', 'root', raw], check=True)
            subprocess.run(['magick', raw, '-crop', '%dx%d+0+0' % (
                dialog.get_width(), dialog.get_height()), '+repage',
                os.path.join(OUT, 'mcomix-library.png')], check=True)
            os.remove(raw)
        finally:
            main_dialog._close_dialog()
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump(2000)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]] + (ONLY or ['Probe']), exit=False)
    sys.stdout.flush()
    os._exit(0)
