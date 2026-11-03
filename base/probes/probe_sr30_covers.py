"""SR 30: covers in a library of many books, through cover size changes.

Each book is a zip holding one picture of a colour unique to it; after
each size change every cover on screen must be its own book's colour,
and every cell must show its own item's cover.
"""
import io
import os
import sys
import unittest
import zipfile

sys.path.insert(0, os.getcwd())
from PIL import Image  # noqa: E402
from test import MComixTest, wait_for, pump  # noqa: E402
from mcomix import constants, icons, image_tools, keybindings, main  # noqa: E402
from mcomix.preferences import prefs  # noqa: E402

COUNT = int(os.environ.get('BOOKS', '1500'))


def colour(index):
    return ((index * 37) % 256, (index * 91) % 256, (index // 7 * 53) % 256)


class Probe(MComixTest):

    def test_sr30(self):
        from mcomix.library import main_dialog
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        prefs['last library collection'] = constants.COLLECTION_ALL
        prefs['lib window width'] = 1200
        prefs['lib window height'] = 900
        icons.load_icons()
        keybindings._manager = None
        folder = os.path.join(self.tmp_dir, 'books')
        os.mkdir(folder)
        paths = []
        for index in range(COUNT):
            data = io.BytesIO()
            Image.new('RGB', (60, 90), colour(index)).save(data, 'PNG')
            path = os.path.join(folder, 'book%05d.zip' % index)
            with zipfile.ZipFile(path, 'w') as book:
                book.writestr('page.png', data.getvalue())
            paths.append(path)
        window = main.MainWindow()
        main.set_main_window(window)
        pump(2000)
        try:
            main_dialog.open_dialog(None, window)
            pump(2000)
            dialog = main_dialog._dialog
            backend = dialog.backend
            with backend.transaction():
                for path in paths:
                    backend.add_book(path)
            area = dialog.book_area
            covers = area._covers
            expected = {}
            for book_id, path in ((backend.get_book_by_path(p).id, p) for p in paths):
                expected[book_id] = colour(int(os.path.basename(path)[4:9]))
            bad_total = 0
            for size in (125, 80, 200, 125, 50, 125):
                prefs['library cover size'] = size
                area.load_covers()
                wait_for(lambda: covers.model.get_n_items() == COUNT, 20)
                for scroll in (0.0, 0.5, 1.0):
                    adj = area.get_vadjustment()
                    adj.set_value(adj.get_lower() + scroll * (adj.get_upper() - adj.get_page_size() - adj.get_lower()))
                    pump(500)
                    cells = [c for c in covers._each_cell() if c.position >= 0]
                    wait_for(lambda: all(covers.get_item(c.position).thumbnail is not None
                                         for c in covers._each_cell() if c.position >= 0), 20)
                    bad = []
                    for cell in covers._each_cell():
                        if cell.position < 0:
                            continue
                        item = covers.get_item(cell.position)
                        shown = cell.picture.get_paintable()
                        if shown is not item.thumbnail:
                            bad.append(('cell shows another paintable', item.uid))
                            continue
                        if shown is None:
                            continue
                        pixbuf = image_tools.texture_to_pixbuf(shown) if hasattr(image_tools, 'texture_to_pixbuf') else None
                        if pixbuf is None:
                            from gi.repository import Gdk
                            downloader = Gdk.TextureDownloader.new(shown)
                            downloader.set_format(Gdk.MemoryFormat.R8G8B8A8)
                            data, stride = downloader.download_bytes()
                            raw = data.get_data()
                            w, h = shown.get_width(), shown.get_height()
                            off = (h // 2) * stride + (w // 2) * 4
                            got = tuple(raw[off:off + 3])
                        else:
                            got = tuple(image_tools.pixbuf_to_pil(pixbuf).convert('RGB').getpixel((pixbuf.get_width() // 2, pixbuf.get_height() // 2)))
                        want = expected[item.uid]
                        if max(abs(a - b) for a, b in zip(got, want)) > 6:
                            bad.append(('colour', item.uid, got, want))
                    bad_total += len(bad)
                    print('size %d scroll %.1f cells %d bad %d %s' % (size, scroll, len(cells), len(bad), bad[:3]), flush=True)
            print('TOTAL BAD', bad_total, flush=True)
        finally:
            main_dialog._close_dialog()
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump(2000)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], 'Probe'], exit=False)
    sys.stdout.flush()
    os._exit(0)
