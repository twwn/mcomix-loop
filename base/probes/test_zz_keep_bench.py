"""How long going back to the book before takes: A, B, then A again."""
import io
import os
import time
import zipfile

from PIL import Image

from . import MComixTest, pump, wait_for
from mcomix import constants
from mcomix import icons
from mcomix import main

PAGES = int(os.environ.get('PAGES', '300'))


class Bench(MComixTest):

    def test_bench(self):
        noise = Image.frombytes('RGB', (1200, 1800), os.urandom(1200 * 1800 * 3))
        page = io.BytesIO()
        noise.save(page, 'JPEG', quality=60)
        books = []
        for name in ('a.cbz', 'b.cbz'):
            book = os.path.join(self.tmp_dir, name)
            with zipfile.ZipFile(book, 'w', zipfile.ZIP_DEFLATED) as out:
                for number in range(PAGES):
                    out.writestr('p%04d.jpg' % number, page.getvalue())
            books.append(book)
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow()
        main.set_main_window(window)
        handler = window.filehandler

        def opened(book):
            start = time.perf_counter()
            assert handler.open_file(book)
            assert wait_for(
                lambda: handler.file_loaded
                and handler._extractor.get_files() == []
                and window.imagehandler.page_is_available(), seconds=40)
            return (time.perf_counter() - start) * 1000

        first = opened(books[0])
        opened(books[1])
        again = opened(books[0])
        print('BENCH %d pages of %d KB: first %.0f ms, again %.0f ms'
              % (PAGES, len(page.getvalue()) // 1024, first, again))
        window.terminate_program()
        window.destroy()
        main.set_main_window(None)
        pump()
