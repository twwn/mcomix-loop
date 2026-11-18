"""Read-back of one library cover at the sizes the library draws: raw
pixels (keep_sized today), zlib level 1 of them, and the stored WebP
decoded by Pillow as thumbnail_tools reads it.  No mcomix import."""
import io, os, statistics, sys, tempfile, time, zlib
from PIL import Image
import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf, GLib

src = Image.open(sys.argv[1]).convert('RGB')
d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR_BENCH'))

def t(f, n=30):
    ts = []
    for _ in range(n):
        a = time.perf_counter(); f(); ts.append(time.perf_counter() - a)
    return statistics.median(ts) * 1000

for h in (125, 250, 500, 1000):
    w = round(src.width * h / src.height)
    img = src.resize((w, h), Image.LANCZOS)
    raw = img.tobytes()
    rowstride = w * 3
    p_raw = os.path.join(d, 'raw%d' % h); open(p_raw, 'wb').write(raw)
    z = zlib.compress(raw, 1)
    p_z = os.path.join(d, 'z%d' % h); open(p_z, 'wb').write(z)
    p_w = os.path.join(d, 'w%d.webp' % h); img.save(p_w, 'WEBP', quality=90, method=4)
    def read_raw():
        b = open(p_raw, 'rb').read()
        GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(b), GdkPixbuf.Colorspace.RGB, False, 8, w, h, rowstride)
    def read_z():
        b = zlib.decompress(open(p_z, 'rb').read())
        GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(b), GdkPixbuf.Colorspace.RGB, False, 8, w, h, rowstride)
    def read_w():
        with open(p_w, 'rb') as f, Image.open(f) as im:
            im = im.convert('RGB'); b = im.tobytes()
            GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(b), GdkPixbuf.Colorspace.RGB, False, 8, w, h, rowstride)
    print('%4d %4dx%-4d raw %7.1f kB %6.3f ms | zlib1 %7.1f kB %6.3f ms (write %.2f ms) | webp %6.1f kB %6.3f ms' % (
        h, w, h, len(raw) / 1000, t(read_raw), len(z) / 1000, t(read_z),
        t(lambda: zlib.compress(raw, 1), 10), os.path.getsize(p_w) / 1000, t(read_w)))
