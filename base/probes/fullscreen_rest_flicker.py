"""Issue 73: with the pointer resting over the page in fullscreen, does a
motion event come after the cursor hides (and so bring it back)?

Puts a real xdotool pointer over the page area, then pumps for PROBE_SECS
without moving it and logs every motion that reaches the event handler and
every cursor drawn.  Run from the checkout (or TREE) under xvfb-run."""
import os, sys, unittest, subprocess, time
from unittest import mock
from gi.repository import Gdk, Graphene
sys.path.insert(0, os.environ.get('TREE') or os.getcwd())
from test import MComixTest, get_testfile_path, pump, wait_for
from mcomix import constants, icons, main


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

    def test_probe(self):
        w = self.window
        w.filehandler.open_file(get_testfile_path('images', 'pattern.jpg'))
        wait_for(lambda: w.imagehandler.page_is_available(), seconds=20)
        pump()
        t0 = time.monotonic()
        log = []
        real_move = w.event_handler.mouse_move_event
        handler = w.cursor_handler
        real_set = w.set_layout_cursor

        def set_layout(mode):
            log.append(('%.2f' % (time.monotonic() - t0), 'cursor',
                        mode.get_name() if mode else None))
            real_set(mode)
        w.set_layout_cursor = set_layout
        real_refresh = handler.refresh

        def refresh():
            log.append(('%.2f' % (time.monotonic() - t0), 'motion'))
            real_refresh()
        handler.refresh = refresh
        fs = mock.patch.object(w, 'is_fullscreen', return_value=True)
        fs.start()
        wayland = bool(os.environ.get('SWAYSOCK'))
        if wayland or os.environ.get('PROBE_REAL_FULLSCREEN'):
            w.fullscreen()
            wait_for(lambda: w.get_surface().get_state() & Gdk.ToplevelState.FULLSCREEN, seconds=5)
            for _ in range(20):
                pump(); time.sleep(0.02)
        print('PROBE backend', type(w.get_display()).__name__, 'renderer', type(w.get_renderer()).__name__)
        area = w.page_area
        aw, ah = area.get_width(), area.get_height()
        ok, pt = area.compute_point(w, Graphene.Point().init(aw / 2, ah / 2))
        sx, sy = w.get_surface_transform()
        if wayland:
            print('PROBE move', subprocess.run(['swaymsg', 'seat', '-', 'cursor', 'set',
                            str(int(pt.x + sx)), str(int(pt.y + sy))], capture_output=True, text=True))
        else:
            xid = w.get_surface().get_xid()
            subprocess.run(['xdotool', 'mousemove', '--window', str(xid),
                            str(int(pt.x + sx)), str(int(pt.y + sy))])
        end = time.monotonic() + float(os.environ.get('PROBE_SECS', '7'))
        while time.monotonic() < end:
            pump()
            time.sleep(0.02)
        fs.stop()
        for entry in log:
            print('PROBE', *entry)
        print('PROBE motions after 1 s:',
              sum(1 for e in log if e[1] == 'motion' and float(e[0]) > 1.0))
        print('PROBE button visible at end:', w.leave_fullscreen_button.widget.get_visible())
        sys.stdout.flush()


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], 'Probe'], exit=False)
    sys.stdout.flush()
    import atexit; atexit._run_exitfuncs()
    os._exit(0)
