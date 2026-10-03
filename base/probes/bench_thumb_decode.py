# Scaled thumbnail decode: gdk-pixbuf new_from_file_at_size against Pillow
# draft(), and load_pixbuf_size as it stands, on a small and a large JPEG
# and a large PNG. Imports mcomix but calls nothing that writes; run with
# HOME and XDG_* pointed into SCRATCH anyway. Run from the checkout, or set
# TREE; the images go to STATE/scratch/thumbbench.
import os, sys, time, zipfile
sys.path.insert(0, os.environ.get('TREE') or os.getcwd())
from PIL import Image
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(os.path.dirname(HERE), 'scratch', 'thumbbench')
os.makedirs(S, exist_ok=True)
zipfile.ZipFile(os.path.join(HERE, 'big60.cbz')).extract('page000.jpg', S)
rng = np.random.default_rng(1)
base = (rng.random((3056, 1988, 3)) * 60 + np.linspace(0, 190, 1988)[None, :, None]).astype('uint8')
Image.fromarray(base).save(os.path.join(S, 'big.jpg'), quality=92)
Image.fromarray(base).save(os.path.join(S, 'big.png'))
import gi
gi.require_version('GdkPixbuf', '2.0'); gi.require_version('Gtk', '4.0')
from gi.repository import GdkPixbuf
from mcomix import image_tools

def gdk(path, w, h):
    return GdkPixbuf.Pixbuf.new_from_file_at_size(path, w, h)
def pil(path, w, h):
    im = Image.open(path); im.draft(None, (w, h))
    return image_tools.fit_in_rectangle(image_tools.pil_to_pixbuf(im, keep_orientation=True), w, h, scaling_quality=GdkPixbuf.InterpType.BILINEAR)
def full(path, w, h):
    return image_tools.load_pixbuf_size(path, w, h)
for name in ('page000.jpg', 'big.jpg', 'big.png'):
    path = os.path.join(S, name)
    for label, fn in (('gdk-pixbuf at_size', gdk), ('Pillow draft', pil), ('load_pixbuf_size', full)):
        fn(path, 128, 128)
        n = 10
        t = time.perf_counter()
        for _ in range(n):
            fn(path, 128, 128)
        print(f'{name:12} {os.path.getsize(path)//1024:6d} KiB  {label:20} {(time.perf_counter()-t)/n*1000:7.1f} ms')
sys.stdout.flush(); os._exit(0)
