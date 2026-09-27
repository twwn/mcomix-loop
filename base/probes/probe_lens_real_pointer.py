"""The lens over an open book: is it drawn, and does it follow a page
turn and a scroll made without moving the pointer?"""
import os, sys, unittest, subprocess, time
from gi.repository import Graphene
sys.path.insert(0, '/tmp/mcomix-git')
from test import MComixTest, get_testfile_path, pump, wait_for
from mcomix import constants, icons, main
from mcomix.preferences import prefs


class Probe(MComixTest):
    def setUp(self):
        super().setUp()
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        self.window = main.MainWindow()
        main.set_main_window(self.window)
        pump()

    def tearDown(self):
        self.window.terminate_program()
        self.window.destroy()
        main.set_main_window(None)
        pump()
        super().tearDown()

    def _lens_pixels(self):
        lens = self.window.lens
        pix = lens._get_lens_pixbuf(*lens._point, (prefs['lens size'],) * 2, 1, (0, 0))
        return bytes(pix.get_pixels())

    def test_probe(self):
        w = self.window
        w.filehandler.open_file(get_testfile_path('images', 'pattern.jpg'))
        wait_for(lambda: w.imagehandler.get_number_of_pages() > 0, seconds=20)
        wait_for(lambda: w.imagehandler.page_is_available(), seconds=20)
        pump()
        print('\nPROBE pages', w.imagehandler.get_number_of_pages(),
              'visible', w.get_visible_area_size())
        w.lens.enabled = True
        area = w.page_area
        aw, ah = area.get_width(), area.get_height()
        ok, pt = area.compute_point(w, Graphene.Point().init(aw / 2, ah / 2))
        sx, sy = w.get_surface_transform()
        xid = w.get_surface().get_xid()
        def slp(n):
            for _ in range(n):
                pump(); time.sleep(0.05)
        subprocess.run(['xdotool', 'mousemove', '--window', str(xid), str(int(pt.x + sx) - 5), str(int(pt.y + sy))])
        slp(5)
        subprocess.run(['xdotool', 'mousemove', '--window', str(xid), str(int(pt.x + sx)), str(int(pt.y + sy))])
        slp(10)
        print('PROBE lens point after real move', w.lens._point)
        pump()
        overlay1 = w.page_area._overlays.get('lens')
        rect1 = w.lens._last_lens_rect
        pix1 = self._lens_pixels()
        print('PROBE after motion: overlay', overlay1 is not None, 'rect', rect1)
        p_before = w.lens._point
        w.flip_page(+1)
        slp(10)
        wait_for(lambda: w.imagehandler.page_is_available(), seconds=20)
        pump()
        overlay2 = w.page_area._overlays.get('lens')
        print('PROBE lens point before/after turn', p_before, w.lens._point)
        pix2 = self._lens_pixels()
        print('PROBE after page turn: page', w.imagehandler.get_current_page(),
              'overlay present', overlay2 is not None,
              'same drawing fn', overlay2 is overlay1,
              'lens content differs from what is shown', pix1 != pix2)
        sys.stdout.flush()


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], 'Probe'], exit=False)
    sys.stdout.flush()
    os._exit(0)
