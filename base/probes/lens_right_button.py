"""Upstream bug 70: middle button held (lens up), right button pressed and
everything released - does the lens stay on?  Real xdotool buttons under
Xvfb.  Built on MComixTest; xvfb-run -s '-screen 0 1280x900x24'."""
import os, subprocess, sys, time, unittest
sys.path.insert(0, os.environ.get('ROOT') or os.getcwd())   # the checkout this runs from, or ROOT
from test import MComixTest, get_testfile_path, pump, wait_for  # noqa: E402
from gi.repository import Graphene, Gtk  # noqa: E402
from mcomix import constants, icons, main  # noqa: E402
OUT = os.environ.get('OUT', '/dev/stderr')


def x(*args):
    subprocess.run(['xdotool', *args], check=True)


class Probe(MComixTest):
    def test_probe(self):
        out = open(OUT, 'a', buffering=1)
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow(open_path=get_testfile_path('archives', '01-ZIP-Normal.zip'))
        main.set_main_window(window)
        wait_for(lambda: window.imagehandler.get_number_of_pages() > 0, seconds=20)
        wait_for(lambda: False, seconds=1)
        area = window.page_area
        ok, p = area.compute_point(window, Graphene.Point().init(area.get_width() / 2, area.get_height() / 2))
        tx, ty = window.get_surface_transform()
        xid = str(window.get_surface().get_xid())
        x('mousemove', '--window', xid, str(int(p.x + tx)), str(int(p.y + ty)))
        lens = window.actiongroup.get_action('lens')
        seen = []
        for widget in (window, area):
            for c in widget.observe_controllers():
                if isinstance(c, Gtk.GestureClick):
                    for sig in ('pressed', 'released', 'stopped', 'cancel', 'unpaired-release'):
                        c.connect(sig, lambda g, *a, sig=sig, w=type(widget).__name__: seen.append('%s:%s:%s' % (w, sig, g.get_current_button())))

        def step(*args):
            x(*args)
            for _ in range(20):
                pump(50)
                time.sleep(0.01)
        cx, cy = int(p.x + tx), int(p.y + ty)
        drag = [('mousedown', '2')] + [('mousemove', '--window', xid, str(cx + d), str(cy + d)) for d in (10, 40, 80, 120)] + [('mouseup', '2')]
        for name, seq in (('middle alone', [('mousedown', '2'), ('mouseup', '2')]),
                          ('middle held and moved 120 px', drag),
                          ('middle, right, release middle, release right',
                           [('mousedown', '2'), ('mousedown', '3'), ('mouseup', '2'), ('mouseup', '3')]),
                          ('middle, right, release right, release middle',
                           [('mousedown', '2'), ('mousedown', '3'), ('mouseup', '3'), ('mouseup', '2')])):
            states = []
            for a in seq:
                step(*a)
                states.append(lens.get_active())
            print('LENS %-48s %s %s' % (name, states, seen), file=out)
            seen.clear()
            window.popup.popdown()
            lens.set_active(False)
            step('mousemove', '--window', xid, str(int(p.x + tx)), str(int(p.y + ty)))
        window.terminate_program(); window.destroy(); main.set_main_window(None); pump()


if __name__ == '__main__':
    unittest.main(argv=['x'], exit=False); sys.stdout.flush(); os._exit(0)
