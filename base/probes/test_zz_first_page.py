"""Time from opening a book of PAGES pages (default 500) to its first
page being available and drawn, in a MainWindow on MComixTest.
Copy into test/ and run with -s.  PROFILE=1 prints the main thread's
cProfile restricted to mcomix, by cumulative time."""
import cProfile, io, os, pstats, time, zipfile

from PIL import Image

from . import MComixTest, wait_for
from mcomix import constants, icons, main


class FirstPageTest(MComixTest):

    def test_first_page(self):
        pages = int(os.environ.get('PAGES', '500'))
        for d in (constants.CONFIG_DIR, constants.DATA_DIR,
                  constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        path = os.path.join(self.tmp_dir, 'big.cbz')
        buf = io.BytesIO()
        Image.effect_noise((800, 1200), 64).convert('RGB').save(buf, 'JPEG')
        data = buf.getvalue()
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as z:
            for i in range(pages):
                z.writestr('p%04d.jpg' % i, data)
        prof = cProfile.Profile() if os.environ.get('PROFILE') else None
        start = time.perf_counter()
        if prof:
            prof.enable()
        window = main.MainWindow(open_path=path)
        main.set_main_window(window)
        listed = wait_for(lambda: window.imagehandler.get_number_of_pages() == pages, 30)
        t_list = time.perf_counter() - start
        shown = wait_for(lambda: window.imagehandler.page_is_available(1), 30)
        t_page = time.perf_counter() - start
        if prof:
            prof.disable()
        print('\nFIRSTPAGE pages=%d listed=%s %.3fs page1=%s %.3fs' % (
            pages, listed, t_list, shown, t_page))
        if prof:
            out = io.StringIO()
            pstats.Stats(prof, stream=out).sort_stats('cumulative').print_stats('mcomix', 25)
            print(out.getvalue())
        window.terminate_program()
        window.destroy()
        main.set_main_window(None)
