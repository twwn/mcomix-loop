import os, statistics, time, unittest.mock, zipfile
from PIL import Image
from . import pump, wait_for
from .test_continuous import _StripTest
from mcomix.preferences import prefs


def _book(path, size, pages, tmp):
    noise = Image.effect_noise((size[0] // 4, size[1] // 4), 60).resize(size).convert('RGB')
    with zipfile.ZipFile(path, 'w') as archive:
        for number in range(pages):
            name = os.path.join(tmp, 'p.jpg')
            noise.rotate(180 if number % 2 else 0).save(name, quality=85)
            archive.write(name, '%03d.jpg' % number)


class Bench(_StripTest):
    PAGES = ((100, 300),) * 2
    VIEW = (1000, 1000)

    def _time(self, label, size, pages, continuous):
        book = os.path.join(self.tmp_dir, 'b%dx%d.zip' % size)
        if not os.path.exists(book):
            _book(book, size, pages, self.tmp_dir)
        prefs['continuous mode'] = continuous
        self.window.filehandler.open_file(book)
        handler = self.window.imagehandler
        assert wait_for(lambda: self.window.filehandler.file_loaded and handler.get_number_of_pages() == pages
                        and all(handler.page_is_available(p) for p in range(1, pages + 1)), seconds=30)
        self._redraw(); pump()
        turns, again = [], []
        for page in range(2, 12):
            start = time.perf_counter()
            self.window.set_page(page)
            if self.window._redraw_source is not None:
                from gi.repository import GLib
                GLib.source_remove(self.window._redraw_source)
            self.window._waiting_for_redraw = True
            self.window._draw_image()
            turns.append((time.perf_counter() - start) * 1000)
            start = time.perf_counter()
            self.window._waiting_for_redraw = True
            self.window._draw_image()
            again.append((time.perf_counter() - start) * 1000)
            pump(200)   # lets the cache thread work, as reading would
        print('BENCH %-34s strip of %2d: turn median %6.1f ms (max %6.1f), same pages again %6.1f ms' % (
            label, self.window.displayed_page_count(), statistics.median(turns), max(turns), statistics.median(again)), flush=True)

    def test_bench(self):
        for size, pages in (((800, 1280), 24), ((800, 300), 40), ((720, 6000), 14)):
            self._time('%dx%d one page' % size, size, pages, False)
            self._time('%dx%d continuous' % size, size, pages, True)
