"""What a MainWindow's widget tree is made of: widgets and controllers
counted by the type of the nearest ancestor that is a popover or menu
bar (or 'window' when there is none).  Built on MComixTest; xvfb-run."""
import collections, os, sys, unittest
sys.path.insert(0, os.environ.get('ROOT') or os.getcwd())   # the checkout this runs from, or ROOT
from test import MComixTest, get_testfile_path, pump, wait_for  # noqa: E402
from gi.repository import Gtk  # noqa: E402
from mcomix import constants, icons, main  # noqa: E402
OUT = os.environ.get('OUT', '/dev/stderr')


class Probe(MComixTest):
    def test_probe(self):
        out = open(OUT, 'a', buffering=1)
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow(open_path=get_testfile_path('archives', '01-ZIP-Normal.zip'))
        main.set_main_window(window)
        wait_for(lambda: window.imagehandler.get_number_of_pages() > 0, seconds=20)
        pump()
        count = collections.Counter()
        controllers = collections.Counter()

        def walk(w, top):
            if isinstance(w, (Gtk.Popover, Gtk.PopoverMenuBar)) and top == 'window':
                top = type(w).__name__
            count[top] += 1
            controllers[top] += len(list(w.observe_controllers()))
            c = w.get_first_child()
            while c is not None:
                walk(c, top)
                c = c.get_next_sibling()
        walk(window, 'window')
        for k in count:
            print('TREE %-18s widgets %5d controllers %5d' % (k, count[k], controllers[k]), file=out)
        window.terminate_program(); window.destroy(); main.set_main_window(None); pump()


if __name__ == '__main__':
    unittest.main(argv=['x'], exit=False); sys.stdout.flush(); os._exit(0)
