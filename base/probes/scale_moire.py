import sys, math
sys.path.insert(0, '.')  # run from the checkout
import gi
gi.require_version('GdkPixbuf', '2.0'); gi.require_version('Gdk', '4.0'); gi.require_version('Gtk', '4.0')
from gi.repository import GdkPixbuf
from PIL import Image
import numpy as np
from mcomix import image_tools
W, H = 2400, 200
s = 0.42
w = int(W * s)
def stripes(period):
    x = np.arange(W)
    row = (127.5 + 100 * np.sin(2 * math.pi * x / period)).astype(np.uint8)
    a = np.repeat(np.tile(row, (H, 1))[:, :, None], 3, axis=2)
    return Image.fromarray(np.ascontiguousarray(a))
def gdk(im, it):
    return np.asarray(image_tools.pixbuf_to_pil(image_tools.pil_to_pixbuf(im).scale_simple(w, int(H*s), GdkPixbuf.InterpType(it))))[:, :, 0].astype(float)
def pil(im, f):
    return np.asarray(im.resize((w, int(H*s)), f))[:, :, 0].astype(float)
# period in source px; target Nyquist is 2/s = 4.76 source px
for period, kind in [(12.0, 'kept (below Nyquist): amplitude retained, ideal 100'), (3.3, 'aliased (above Nyquist): residual amplitude, ideal 0')]:
    im = stripes(period)
    print(kind, 'period', period)
    for name, f in [('gdk TILES', lambda: gdk(im, 1)), ('gdk BILINEAR', lambda: gdk(im, 2)), ('gdk HYPER', lambda: gdk(im, 3)),
                    ('PIL BICUBIC', lambda: pil(im, Image.Resampling.BICUBIC)), ('PIL LANCZOS', lambda: pil(im, Image.Resampling.LANCZOS))]:
        a = f()[:, 10:-10]
        print('  %-13s %.1f' % (name, (a.max() - a.min()) / 2))
