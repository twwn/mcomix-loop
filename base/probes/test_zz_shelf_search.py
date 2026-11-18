"""Probe: real key presses (xdotool, inside Xvfb) for the shelf's search:
CTRL+F, a name typed with letters that are shortcuts, a shortcut the
field leaves, Escape.  Prints what the shelf shows and which shortcuts
ran after each step (fullscreen cannot be seen without a window
manager)."""
import os
import shutil
import subprocess
import time

from gi.repository import Gtk

from test import get_testfile_path, pump, wait_for
from test.test_shelf import _ShelfWindowTest

from mcomix import constants
from mcomix import keybindings
from mcomix.library import backend


def spin(n=25):
    for _ in range(n):
        pump()
        time.sleep(0.01)


class ShelfSearchProbe(_ShelfWindowTest):

    def test_probe(self):
        library = backend.LibraryBackend()
        names = ('fafnir.zip', 'dragon.zip', 'other.zip')
        for name in names:
            path = os.path.join(self.tmp_dir, name)
            shutil.copy(get_testfile_path('archives', '01-ZIP-Normal.zip'), path)
            library.add_book(path)
        # One read: the shelf shows "Recent", which holds only that one.
        library.add_book_to_collection(
            library.get_book_by_path(os.path.join(self.tmp_dir, 'other.zip')).id,
            constants.COLLECTION_RECENT)
        library.close()
        window = self._window()
        window.present()
        self.assertTrue(wait_for(lambda: window.get_mapped()))
        shelf = self._shown()
        area = shelf.book_area
        spin(40)
        area.focus_covers()
        spin()

        manager = keybindings.keybinding_manager(window)
        original = manager.execute
        ran = []

        def execute(accel):
            ran.append(Gtk.accelerator_name(*accel))
            return original(accel)
        manager.execute = execute

        def state(what):
            print('PROBE', what, 'ran', ran[:],
                  shelf._heading.get_text(),
                  sorted(os.path.basename(p) for p in area.shown_paths()),
                  'bar', shelf._search_bar.get_search_mode(),
                  'text', repr(shelf._search.get_text()),
                  'focus', type(window.get_focus()).__name__)
            ran.clear()

        found = subprocess.run(['xdotool', 'search', '--name', 'MComix'],
                               capture_output=True, text=True, timeout=10)
        xid = found.stdout.split()[-1]
        subprocess.run(['xdotool', 'windowfocus', xid], timeout=10)
        spin()
        state('START')
        for keys in (['ctrl+f'], ['f', 'a', 'f'],
                     ['BackSpace', 'BackSpace', 'BackSpace', 'd', 'r'],
                     ['F11'], ['Escape'], ['f'], ['ctrl+f'], ['Escape']):
            for key in keys:
                subprocess.run(['xdotool', 'key', key], timeout=10)
                spin(5)
            spin(60)  # past the search's delay
            state('after ' + ' '.join(keys))
