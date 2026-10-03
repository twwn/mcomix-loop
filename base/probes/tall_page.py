"""Does a very tall page show at 100% zoom?  Upstream bug 152: a 1x40000
image did not.  Builds a folder with one W x H PNG (red top, blue bottom),
opens it at manual zoom 100 %, screenshots the screen and prints the colour
at the top of the page area.  W, H and GSK_RENDERER come from the
environment.  Built on MComixTest; run under xvfb-run -s '-screen 0
1280x900x24' with a timeout."""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.environ.get('ROOT') or os.getcwd())   # the checkout this runs from, or ROOT
from test import MComixTest, pump, wait_for  # noqa: E402

from gi.repository import Graphene  # noqa: E402
from PIL import Image  # noqa: E402

from mcomix import constants, icons, main, theme  # noqa: E402
from mcomix.preferences import prefs  # noqa: E402

W = int(os.environ.get('W', '600'))
H = int(os.environ.get('H', '40000'))
OUT = os.environ.get('OUT', '/dev/stderr')


class Probe(MComixTest):

    def test_probe(self):
        out = open(OUT, 'a', buffering=1)
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        book = os.path.join(self.tmp_dir, 'book')
        os.makedirs(book)
        img = Image.new('RGB', (W, H), (255, 0, 0))
        img.paste((0, 0, 255), (0, H // 2, W, H))
        img.save(os.path.join(book, 'p.png'))
        icons.load_icons()
        theme.follow_theme()
        prefs['zoom mode'] = constants.ZoomMode.MANUAL
        prefs['show thumbnails'] = False
        window = main.MainWindow(open_path=os.path.join(book, 'p.png'))
        main.set_main_window(window)
        wait_for(lambda: window.imagehandler.get_number_of_pages() > 0, seconds=20)
        window.manual_zoom_original()
        wait_for(lambda: False, seconds=3)
        renderer = type(window.get_native().get_renderer()).__name__
        shot = os.path.join(self.tmp_dir, 'shot.png')
        subprocess.run(['import', '-window', 'root', shot], check=True)
        area = window.page_area
        ok, point = area.compute_point(window, Graphene.Point().init(area.get_width() / 2, 20))
        px = Image.open(shot).convert('RGB').getpixel((int(point.x), int(point.y)))
        print('TALL %dx%d renderer=%s content=%s pixel=%s' % (
            W, H, renderer, area.get_content_size(), px), file=out)
        window.terminate_program()
        window.destroy()
        main.set_main_window(None)
        pump()


if __name__ == '__main__':
    unittest.main(argv=['x'], exit=False)
    sys.stdout.flush()
    os._exit(0)
