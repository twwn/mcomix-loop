"""Time opening one book directly (as from a file manager or the command
line) in a folder of SIBLINGS other books and SUBDIRS subfolders of 20
books each, against opening it from a list (as the library does).
Copy into test/ and run with -s.  PROFILE=1 prints a cProfile restricted
to mcomix, by cumulative time, for the direct open.  RUNS opens each way
RUNS times, alternating, into a window already built."""
import cProfile, io, os, pstats, time, zipfile

from PIL import Image

from . import MComixTest, wait_for, pump
from mcomix import constants, icons, main


def _zip(path, data, pages=3):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as z:
        for i in range(pages):
            z.writestr('p%02d.jpg' % i, data)


class OpenDirectTest(MComixTest):

    def test_open_direct(self):
        siblings = int(os.environ.get('SIBLINGS', '2000'))
        subdirs = int(os.environ.get('SUBDIRS', '50'))
        runs = int(os.environ.get('RUNS', '5'))
        for d in (constants.CONFIG_DIR, constants.DATA_DIR,
                  constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        buf = io.BytesIO()
        Image.effect_noise((800, 1200), 64).convert('RGB').save(buf, 'JPEG')
        data = buf.getvalue()
        shelf = os.path.join(self.tmp_dir, 'shelf')
        folder = os.path.join(shelf, 'series')
        os.makedirs(folder)
        books = []
        for i in range(siblings):
            p = os.path.join(folder, 'book %04d.cbz' % i)
            _zip(p, data, 1)
            books.append(p)
        for d in range(subdirs):
            sub = os.path.join(shelf, 'other %03d' % d)
            os.makedirs(sub)
            for i in range(20):
                _zip(os.path.join(sub, 'b%02d.cbz' % i), data, 1)
        targets = [books[len(books) // 2], books[len(books) // 2 + 1]]
        # As books on a shelf are: written long before they are read
        # (archive_tools keeps nothing of a file written seconds ago).
        old = time.time() - 3600
        for root, _dirs, files in os.walk(shelf):
            for name in files:
                os.utime(os.path.join(root, name), (old, old))
        window = main.MainWindow()
        main.set_main_window(window)
        pump()
        handler = window.filehandler

        def opened(path):
            return wait_for(
                lambda: handler.get_path_to_base() == path
                and window.imagehandler.page_is_available(1), 30)

        times = {'direct': [], 'listed': []}
        prof = cProfile.Profile() if os.environ.get('PROFILE') else None
        for run in range(runs):
            for mode in ('direct', 'listed'):
                path = targets[(run + (mode == 'listed')) % 2]
                start = time.perf_counter()
                if prof and mode == 'direct':
                    prof.enable()
                if mode == 'direct':
                    handler.open_file(path)
                else:
                    handler.open_file(path, listed=books)
                ok = opened(path)
                if prof and mode == 'direct':
                    prof.disable()
                times[mode].append((time.perf_counter() - start) * 1000)
                assert ok, (mode, path)
                # The neighbours, as Next would walk them.
                t = time.perf_counter()
                handler._file_provider.list_files(handler._file_provider.ARCHIVES)
                times.setdefault(mode + ' list_files', []).append(
                    (time.perf_counter() - t) * 1000)
        for mode, ms in times.items():
            ms = sorted(ms)
            print('\nOPEN %s: median %.1f ms, min %.1f, max %.1f (%d runs)'
                  % (mode, ms[len(ms) // 2], ms[0], ms[-1], len(ms)))
        if prof:
            out = io.StringIO()
            st = pstats.Stats(prof, stream=out).sort_stats('cumulative')
            st.print_stats('mcomix', 30)
            print(out.getvalue())
        window.terminate_program()
