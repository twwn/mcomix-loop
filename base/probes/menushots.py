"""Shots of each menu bar menu, the right-click menu and the preference tabs."""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.getcwd())
OUT = sys.argv.pop(1)
ONLY_DIALOGS = 'dialogs' in sys.argv[1:]
sys.argv = sys.argv[:1]

from gi.repository import Gtk, Graphene  # noqa: E402

from test import MComixTest, wait_for, pump  # noqa: E402
from mcomix import constants, icons, keybindings, main, theme, preferences_dialog  # noqa: E402
from mcomix.preferences import prefs  # noqa: E402

BOOK = os.path.join(os.getcwd(), 'test', 'files', 'pepper-and-carrot',
                    'Pepper-and-Carrot_E01_The-Potion-of-Flight.cbz')


def shot(name, geom='1280x1000+0+0'):
    raw = os.path.join(OUT, 'raw.png')
    subprocess.run(['import', '-window', 'root', raw], check=True)
    subprocess.run(['magick', raw, '-crop', geom, '+repage',
                    os.path.join(OUT, name + '.png')], check=True)
    os.remove(raw)


class Probe(MComixTest):

    def test_menus(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        prefs['show toolbar'] = True
        prefs['show menubar'] = True
        prefs['show statusbar'] = True
        prefs['show thumbnails'] = True
        prefs['window width'] = 1280
        prefs['window height'] = 1000
        prefs['colour scheme'] = theme.LIGHT
        theme.follow_theme()
        icons.load_icons()
        keybindings._manager = None
        window = main.MainWindow(open_path=BOOK)
        main.set_main_window(window)
        try:
            window.set_decorated(False)
            window.present()
            pump(2000)
            wait_for(lambda: False, seconds=2)
            bar = window.menubar
            child = bar.get_first_child()
            items = []
            while child is not None:
                ok, r = child.compute_bounds(window)
                items.append(r)
                child = child.get_next_sibling()
            for i, r in (enumerate(items) if not ONLY_DIALOGS else ()):
                x = int(r.get_x() + r.get_width() / 2)
                y = int(r.get_y() + r.get_height() / 2)
                subprocess.run(['xdotool', 'mousemove', str(x), str(y), 'click', '1'])
                wait_for(lambda: False, seconds=1)
                shot('menubar-%d' % i)
                subprocess.run(['xdotool', 'key', 'Escape'])
                wait_for(lambda: False, seconds=0.5)
            subprocess.run(['xdotool', 'mousemove', '1270', '990'])
            area = window.page_area
            if not ONLY_DIALOGS: window.show_page_menu(area, 300, 100, window.imagehandler.get_current_page())
            wait_for(lambda: False, seconds=1)
            shot('popup')
            window.popup.popdown()
            for name in ('enhance_image', 'properties', 'go_to', 'about', 'comments'):
                window.actiongroup.get_action(name).activate()
                wait_for(lambda: False, seconds=1.5)
                shot('dialog-' + name)
                for top in Gtk.Window.list_toplevels():
                    if top is not window and top.get_visible():
                        top.close()
                wait_for(lambda: False, seconds=0.5)
            if ONLY_DIALOGS:
                return
            preferences_dialog.open_dialog(None, window)
            dialog = preferences_dialog._dialog
            wait_for(lambda: False, seconds=1)
            nb = dialog.get_child().get_first_child() if False else None
            # find notebook
            def find(w):
                if isinstance(w, Gtk.Notebook):
                    return w
                c = w.get_first_child()
                while c is not None:
                    f = find(c)
                    if f is not None:
                        return f
                    c = c.get_next_sibling()
                return None
            nb = find(dialog)
            for n in range(nb.get_n_pages()):
                nb.set_current_page(n)
                wait_for(lambda: False, seconds=1)
                print('prefs', n, dialog.get_width(), dialog.get_height(), flush=True)
                shot('prefs-%d' % n)
            preferences_dialog._close_dialog()
        finally:
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump(2000)


if __name__ == '__main__':
    unittest.main(argv=sys.argv[:1])
    sys.stdout.flush()
    os._exit(0)
