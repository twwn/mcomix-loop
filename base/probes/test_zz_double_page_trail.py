import os, shutil, zipfile
from . import MComixTest, get_testfile_path, pump, wait_for
from mcomix import constants, icons, main
from mcomix.preferences import prefs

N = get_testfile_path('images', 'portrait-no-exif.png')
W = get_testfile_path('images', 'landscape-no-exif.png')
R = get_testfile_path('images', 'landscape-exif-270-rotation.jpg')
J = get_testfile_path('images', 'portrait-no-exif.jpg')
SRC = {'N': N, 'W': W, 'R': R, 'J': J}

class Probe(MComixTest):
    def _run(self, layout, as_archive, moves):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        prefs['default double page'] = True
        book = os.path.join(self.tmp_dir, layout + ('.cbz' if as_archive else ''))
        if as_archive:
            with zipfile.ZipFile(book, 'w') as z:
                for i, kind in enumerate(layout, 1):
                    z.write(SRC[kind], '%02d%s' % (i, os.path.splitext(SRC[kind])[1]))
        else:
            os.mkdir(book)
            for i, kind in enumerate(layout, 1):
                shutil.copy(SRC[kind], os.path.join(book, '%02d%s' % (i, os.path.splitext(SRC[kind])[1])))
            book = os.path.join(book, sorted(os.listdir(book))[0])
        window = main.MainWindow(open_path=book)
        main.set_main_window(window)
        try:
            h = window.imagehandler
            wait_for(lambda: h.get_number_of_pages() == len(layout), seconds=20)
            wait_for(lambda: all(h.page_is_available(p) for p in range(1, len(layout) + 1)), seconds=20)
            pump()
            def shown():
                c = h.get_current_page()
                return '%s%s' % (c, '+%d' % (c + 1) if window.displayed_double() else '')
            trail = [shown()]
            n = len(layout)
            while h.get_current_page() + (1 if window.displayed_double() else 0) < n:
                window.flip_page(1); pump(); trail.append('>' + shown())
            while h.get_current_page() > 1:
                window.flip_page(-1); pump(); trail.append('<' + shown())
            print('PROBE %s %s: %s' % ('archive' if as_archive else 'directory', ''.join(layout), ' '.join(trail)))
        finally:
            window.terminate_program(); window.destroy(); main.set_main_window(None); pump()
    def test_many(self):
        for layout in ('JJRRJ', 'JJJRRJ', 'JJJJRRJ', 'NNRRN', 'NNNRRN'):
            for arch in (False, True):
                self._run(layout, arch, [1] * 6 + [-1] * 6)
