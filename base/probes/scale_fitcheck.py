import sys, time, random
sys.path.insert(0, '.')  # run from the checkout
import gi
gi.require_version('GdkPixbuf', '2.0'); gi.require_version('Gdk', '4.0'); gi.require_version('Gtk', '4.0')
from PIL import Image, ImageDraw
import numpy as np
from mcomix import image_tools, constants
art = Image.new('RGB', (2400, 3400), 'white')
dr = ImageDraw.Draw(art); random.seed(1)
for _ in range(400):
    dr.line([(random.randrange(2400), random.randrange(3400)) for _ in range(2)], fill=(0, 0, 0), width=random.randrange(1, 6))
def t(f, n=5):
    best = 1e9
    for _ in range(n):
        a = time.perf_counter(); f(); best = min(best, time.perf_counter() - a)
    return best * 1000
for im, dst in ((art, (1008, 1428)), (art.resize((1200, 1800)), (853, 1280)), (art.resize((800, 1200)), (1280, 1920)), (art.resize((6000, 9000)), (800, 1200)), (art.convert('RGBA'), (1008, 1428))):
    for q, f in ((constants.SCALING_LANCZOS, Image.Resampling.LANCZOS), (constants.SCALING_BICUBIC, Image.Resampling.BICUBIC)):
        src = image_tools.pil_to_pixbuf(im)
        out = np.asarray(image_tools.pixbuf_to_pil(image_tools.fit_in_rectangle(src, *dst, scale_up=True, keep_ratio=False, scaling_quality=q)).convert('RGB'), dtype=int)
        ref = np.asarray(im.resize(dst, f, reducing_gap=3.0).convert('RGB'), dtype=int)
        print(im.size, im.mode, dst, f.name, 'max diff vs Pillow alone', np.abs(out - ref).max(), 'fit %.1f ms' % t(lambda: image_tools.fit_in_rectangle(src, *dst, scale_up=True, keep_ratio=False, scaling_quality=q)))
