"""Does the status bar's height follow its text?  Upstream bug 148: CJK
file names made it taller.  Measures the Statusbar's natural height with
Latin, CJK, Arabic and emoji text.  Built on MComixTest; xvfb-run."""
import os
import sys
import unittest

sys.path.insert(0, os.environ.get('ROOT') or os.getcwd())   # the checkout this runs from, or ROOT
from test import MComixTest, pump  # noqa: E402

from gi.repository import Gtk  # noqa: E402

from mcomix import status  # noqa: E402

OUT = os.environ.get('OUT', '/dev/stderr')


class Probe(MComixTest):

    def test_probe(self):
        out = open(OUT, 'a', buffering=1)
        window = Gtk.Window()
        bar = status.Statusbar()
        window.set_child(bar)
        window.present()
        pump()
        for name, text in (('latin', 'Volume 01 - page 003.jpg'),
                           ('cjk', '進撃の巨人 第01巻 003.jpg'),
                           ('hangul', '나 혼자만 레벨업 003.jpg'),
                           ('arabic', 'المجلد ٠١.jpg'),
                           ('emoji', 'volume 😀 01.jpg')):
            bar.set_filename(text)
            bar.update()
            pump()
            minimum, natural, _b, _c = bar.measure(Gtk.Orientation.VERTICAL, -1)
            print('STATUS %-7s min=%d nat=%d' % (name, minimum, natural), file=out)
        window.destroy()
        pump()


if __name__ == '__main__':
    unittest.main(argv=['x'], exit=False)
    sys.stdout.flush()
    os._exit(0)
