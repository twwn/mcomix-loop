import os, subprocess, time, zipfile
from gi.repository import Graphene
from PIL import Image
from . import MComixTest, pump, wait_for
from mcomix import constants, icons, keybindings, main
from mcomix.preferences import prefs


def settle(n=8):
    for _ in range(n):
        pump(); time.sleep(0.02)


def xdo(*args):
    subprocess.run(('xdotool',) + tuple(str(a) for a in args), check=True)


class Probe(MComixTest):
    def setUp(self):
        super().setUp()
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        prefs['continuous mode'] = True
        prefs['continuous width'] = 50
        icons.load_icons()
        keybindings._manager = None
        book = os.path.join(self.tmp_dir, 'strip.zip')
        with zipfile.ZipFile(book, 'w') as archive:
            for number in range(1, 9):
                name = os.path.join(self.tmp_dir, 'page.png')
                Image.new('RGB', (300, 900), (number * 30, 0, 0)).save(name)
                archive.write(name, '%02d.png' % number)
        self.window = main.MainWindow(open_path=book)
        main.set_main_window(self.window)
        handler = self.window.imagehandler
        assert wait_for(lambda: all(handler.page_is_available(p) for p in range(1, 9)), seconds=20)
        self.window.present(); settle(30)

    def tearDown(self):
        self.window.terminate_program(); self.window.destroy(); main.set_main_window(None); pump()
        super().tearDown()

    def _doc(self):
        height = self.window.layout.get_content_boxes()[0].get_size()[1]
        return (self.window.imagehandler.get_current_page() - 1) * height + self.window.page_area.get_vadjustment().get_value(), height

    def test_bar(self):
        """A real click in the scroll bar's trough pages the strip down; a
        slider drag by xdotool does not move a GtkRange under Xvfb, in a
        strip or out of one, so the trough is what a probe can press."""
        prefs['show scrollbar'] = True
        area = self.window.page_area
        bar = self.window._scroll[constants.PageAxis.HEIGHT]
        settle(10)
        ok, pt = bar.compute_point(self.window, Graphene.Point().init(bar.get_width() / 2, bar.get_height() - 10))
        dx, dy = self.window.get_surface_transform()
        xid = self.window.get_surface().get_xid()
        xdo('mousemove', '--window', xid, int(pt.x + dx), int(pt.y + dy)); settle(5)
        offsets = [self._doc()[0]]; pages = [1]
        for _ in range(12):
            xdo('click', 1); settle(12)
            offsets.append(self._doc()[0]); pages.append(self.window.imagehandler.get_current_page())
        steps = [round(b - a) for a, b in zip(offsets, offsets[1:])]
        print('PROBE 12 clicks in the trough below the slider: pages', pages, 'steps', steps, 'final offset', round(offsets[-1]))
    def test_wheel(self):
        area = self.window.page_area
        ok, pt = area.compute_point(self.window, Graphene.Point().init(area.get_width() / 2, area.get_height() / 2))
        dx, dy = self.window.get_surface_transform()
        xid = self.window.get_surface().get_xid()
        xdo('mousemove', '--window', xid, int(pt.x + dx), int(pt.y + dy)); settle(5)
        print('PROBE view', area.get_width(), area.get_height(), 'strip of', self.window.displayed_page_count(), 'page height', self._doc()[1])
        offsets = [self._doc()[0]]; pages = [1]
        for _ in range(60):
            xdo('click', 5); settle(6)
            offsets.append(self._doc()[0]); pages.append(self.window.imagehandler.get_current_page())
        steps = [round(b - a) for a, b in zip(offsets, offsets[1:])]
        print('PROBE down: pages reached', sorted(set(pages)), 'steps', sorted(set(steps)), 'final offset', round(offsets[-1]))
        offsets = [self._doc()[0]]; pages = []
        for _ in range(60):
            xdo('click', 4); settle(6)
            offsets.append(self._doc()[0]); pages.append(self.window.imagehandler.get_current_page())
        steps = [round(b - a) for a, b in zip(offsets, offsets[1:])]
        print('PROBE up: pages reached', sorted(set(pages)), 'steps', sorted(set(steps)), 'final offset', round(offsets[-1]))
