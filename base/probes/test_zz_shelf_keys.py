"""Probe: real key presses (xdotool, inside Xvfb) on the main window's
shelf of covers; which cover is selected after each."""
import os
import shutil
import subprocess

from test import get_testfile_path, pump, wait_for
from test.test_shelf import _ShelfWindowTest

from mcomix.library import backend


class ShelfKeysProbe(_ShelfWindowTest):

    def test_probe(self):
        library = backend.LibraryBackend()
        for index in range(15):
            path = os.path.join(self.tmp_dir, 'book%02d.zip' % index)
            shutil.copy(get_testfile_path('archives', '01-ZIP-Normal.zip'), path)
            library.add_book(path)
        library.close()
        window = self._window()
        window.present()
        self.assertTrue(wait_for(lambda: window.get_mapped()))
        area = self._shown().book_area
        self.assertTrue(wait_for(lambda: len(area.shown_ids()) == 15))
        for _ in range(30):
            pump()
        area._covers.grab_focus()
        area._covers.get_model().select_item(0, True)
        pump()
        ids = area.shown_ids()

        def at():
            selected = area._selected_items()
            return [ids.index(item.uid) for item in selected]

        print('PROBE START', at(), 'focus', type(window.get_focus()).__name__)
        found = subprocess.run(['xdotool', 'search', '--name', 'MComix'],
                               capture_output=True, text=True, timeout=10)
        print('PROBE SEARCH', found.returncode, repr(found.stdout[-60:]),
              repr(found.stderr[-200:]))
        xid = found.stdout.split()[-1] if found.stdout.split() else None
        if xid:
            focused = subprocess.run(['xdotool', 'windowfocus', xid],
                                     capture_output=True, text=True, timeout=10)
            print('PROBE FOCUS', focused.returncode, repr(focused.stderr[-200:]))
        for _ in range(20):
            pump()
        for key in ('Down', 'Down', 'Up', 'Right', 'End', 'Home'):
            sent = subprocess.run(['xdotool', 'key', key], check=False,
                                  timeout=10, capture_output=True, text=True)
            if sent.returncode:
                print('PROBE KEY FAILED', sent.stderr[-200:])
            for _ in range(20):
                pump()
            print('PROBE', key, at())
