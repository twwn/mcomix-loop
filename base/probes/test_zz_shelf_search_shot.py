"""Probe: a screenshot of the shelf with its search field open, as the
X server draws it (ImageMagick's import inside Xvfb).  PROBE_SHOT names
the PNG; PROBE_THEME 'dark' prefers the dark scheme."""
import os
import shutil
import subprocess
import time

from gi.repository import Gtk

from test import get_testfile_path, pump, wait_for
from test.test_shelf import _ShelfWindowTest

from mcomix import constants
from mcomix.library import backend


def spin(n=25):
    for _ in range(n):
        pump()
        time.sleep(0.01)


class ShelfSearchShot(_ShelfWindowTest):

    def test_probe(self):
        if os.environ.get('PROBE_THEME') == 'dark':
            Gtk.Settings.get_default().set_property(
                'gtk-application-prefer-dark-theme', True)
        library = backend.LibraryBackend()
        for index in range(12):
            path = os.path.join(self.tmp_dir, 'book%02d.zip' % index)
            shutil.copy(get_testfile_path('archives', '01-ZIP-Normal.zip'), path)
            library.add_book(path)
        library.add_book_to_collection(
            library.get_book_by_path(os.path.join(self.tmp_dir, 'book00.zip')).id,
            constants.COLLECTION_RECENT)
        library.close()
        window = self._window()
        window.set_default_size(900, 600)
        window.present()
        self.assertTrue(wait_for(lambda: window.get_mapped()))
        shelf = self._shown()
        spin(60)
        shot = os.environ.get('PROBE_SHOT', '/tmp/shelf.png')

        def grab(suffix):
            spin(60)
            result = subprocess.run(
                ['import', '-window', 'root', shot.replace('.png', suffix + '.png')],
                capture_output=True, text=True, timeout=20)
            print('PROBE', suffix, 'import', result.returncode, result.stderr.strip())

        grab('-closed')
        cover_y = shelf.book_area.compute_bounds(window)[1].get_y()
        shelf.search()
        spin(60)
        shelf._search.set_text('book0')
        shelf._search.emit('activate')
        grab('-open')
        print('PROBE covers y closed', cover_y, 'open',
              shelf.book_area.compute_bounds(window)[1].get_y(),
              'bar', shelf._search_bar.compute_bounds(window)[1].get_x(),
              shelf._search_bar.compute_bounds(window)[1].get_width(),
              'window', window.get_width())
