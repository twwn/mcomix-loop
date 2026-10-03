"""Decode times of one page as WebP, PNG and JPEG: MComix' load_pixbuf,
Pillow alone, and gdk-pixbuf alone.  Upstream bug 160: WebP 2.7x slower
than PNG.  DIR holds p.webp, p.png, p.jpg.  Median of 5; xvfb-run."""
import os, statistics, sys, time
sys.path.insert(0, os.environ.get('ROOT') or os.getcwd())   # the checkout this runs from, or ROOT
import gi
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '4.0')
from gi.repository import GdkPixbuf  # noqa: E402
from PIL import Image  # noqa: E402
from mcomix import image_tools  # noqa: E402

D = os.environ['DIR']


def t(f):
    xs = []
    for _ in range(5):
        a = time.perf_counter(); f(); xs.append(time.perf_counter() - a)
    return statistics.median(xs)


for ext in ('webp', 'png', 'jpg'):
    p = os.path.join(D, 'p.' + ext)
    def pil():
        with Image.open(p) as im:
            im.load()
    def pil_path():
        return image_tools.pil_to_pixbuf(image_tools._in_srgb(Image.open(p)),
                                         keep_orientation=True)
    print('%-4s load_pixbuf %.3f  pillow %.3f  pillow->pixbuf %.3f  gdkpixbuf %.3f' % (
        ext, t(lambda: image_tools.load_pixbuf(p)), t(pil), t(pil_path),
        t(lambda: GdkPixbuf.Pixbuf.new_from_file(p))), flush=True)
os._exit(0)
