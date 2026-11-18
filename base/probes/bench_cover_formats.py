"""Size, encode and decode time of a library cover (fit in 500x500, as
LIBRARY_COVERS_PATH stores it) in PNG and in the alternatives.

python3 -I bench_cover_formats.py <out dir> <picture>...  Synthetic
comic-like covers are added.  Decode is Pillow's open + load on one
thread, median of REPS; JXL goes through cjxl/djxl (no Pillow codec),
its decode timed by djxl --num_reps, so not comparable to the rest to
better than a factor."""
import io
import os
import random
import statistics
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFilter

REPS = 15
from PIL import AvifImagePlugin
if os.environ.get("AVIF_DEC"):
    AvifImagePlugin.DECODE_CODEC_CHOICE = os.environ["AVIF_DEC"]
if os.environ.get("AVIF_THREADS"):
    AvifImagePlugin.DEFAULT_MAX_THREADS = int(os.environ["AVIF_THREADS"])
print("avif decoder", AvifImagePlugin.DECODE_CODEC_CHOICE, "threads", AvifImagePlugin.DEFAULT_MAX_THREADS)
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'


def synthetic(seed):
    """Flat fills, black outlines, a gradient sky, lettering, halftone
    dots, then saved as a JPEG at 85 as the book holds it and read back."""
    rng = random.Random(seed)
    w, h = 1000, 1500
    img = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(img)
    top, bottom = [rng.randrange(256) for _ in range(3)], [rng.randrange(256) for _ in range(3)]
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    for _ in range(25):
        x0, y0 = rng.randrange(w), rng.randrange(h)
        x1, y1 = x0 + rng.randrange(50, 400), y0 + rng.randrange(50, 400)
        colour = tuple(rng.randrange(256) for _ in range(3))
        if rng.random() < 0.5:
            d.ellipse([x0, y0, x1, y1], fill=colour, outline='black', width=6)
        else:
            d.polygon([(x0, y0), (x1, y0 + 30), (x1 - 40, y1), (x0 + 20, y1 - 10)], fill=colour, outline='black', width=6)
    for _ in range(6):
        x0, y0 = rng.randrange(w), rng.randrange(h)
        for yy in range(y0, min(h, y0 + 200), 12):
            for xx in range(x0, min(w, x0 + 300), 12):
                d.ellipse([xx, yy, xx + 6, yy + 6], fill='black')
    d.rectangle([0, 0, w, 220], fill=(200, 20, 30))
    for i in range(12):
        d.text((40 + i * 70, 60), 'AB'[i % 2], fill='white', font_size=120)
    for _ in range(300):
        x, y = rng.randrange(w), rng.randrange(h)
        d.line([(x, y), (x + rng.randrange(-60, 60), y + rng.randrange(-60, 60))], fill='black', width=2)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    data = io.BytesIO()
    img.save(data, 'JPEG', quality=85)
    return Image.open(io.BytesIO(data.getvalue())).convert('RGB')


def covers():
    for path in sys.argv[2:]:
        try:
            with Image.open(path) as img:
                picture = img.convert('RGB')
        except OSError:
            continue
        yield os.path.basename(path)[:24], picture
    for seed in range(4):
        yield 'synthetic%d' % seed, synthetic(seed)


def fit(img):
    img = img.copy()
    img.thumbnail((500, 500), Image.Resampling.LANCZOS)
    return img


def timed(fn):
    times = []
    for _ in range(REPS):
        begun = time.perf_counter()
        fn()
        times.append(time.perf_counter() - begun)
    return statistics.median(times) * 1000


FORMATS = [
    ('png6', 'PNG', {'compress_level': 6}),
    ('webp-lossless', 'WEBP', {'lossless': True, 'quality': 80, 'method': 4}),
    ('webp-q90', 'WEBP', {'quality': 90, 'method': 4}),
    ('webp-q80', 'WEBP', {'quality': 80, 'method': 4}),
    ('avif-q90', 'AVIF', {'quality': 90}),
    ('avif-q75', 'AVIF', {'quality': 75}),
    ('jpeg-q90', 'JPEG', {'quality': 90}),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    totals = {}
    for name, img in covers():
        cover = fit(img)
        line = ['%-24s %dx%d' % (name, *cover.size)]
        for label, fmt, options in FORMATS:
            data = io.BytesIO()
            enc = timed(lambda: cover.save(io.BytesIO(), fmt, **options))
            cover.save(data, fmt, **options)
            raw = data.getvalue()
            dec = timed(lambda: Image.open(io.BytesIO(raw)).load())
            totals.setdefault(label, []).append((len(raw), enc, dec))
            line.append('%s %.0fkB e%.1f d%.2f' % (label, len(raw) / 1000, enc, dec))
        # JPEG XL through the command line tools.
        src = os.path.join(OUT, 'cover.png')
        cover.save(src)
        for label, args in (('jxl-lossless', ['-d', '0', '-e', '7']), ('jxl-d1', ['-d', '1', '-e', '7'])):
            dst = os.path.join(OUT, 'cover.jxl')
            begun = time.perf_counter()
            subprocess.run(['cjxl', src, dst, *args, '--quiet'], check=True, capture_output=True)
            enc = (time.perf_counter() - begun) * 1000
            out = subprocess.run(['djxl', dst, '--num_reps', '20', '--num_threads', '0', os.path.join(OUT, 'back.png')], capture_output=True, text=True)
            speed = [w for w in (out.stdout + out.stderr).split() if 'MP/s' in w or w.replace('.', '', 1).isdigit()]
            mp = None
            for token in (out.stdout + out.stderr).replace(',', ' ').split():
                pass
            import re
            found = re.findall(r'([0-9.]+) MP/s', out.stdout + out.stderr)
            dec = cover.size[0] * cover.size[1] / 1e6 / float(found[-1]) * 1000 if found else float('nan')
            size = os.path.getsize(dst)
            totals.setdefault(label, []).append((size, enc, dec))
            line.append('%s %.0fkB e%.0f(cli) d%.2f' % (label, size / 1000, enc, dec))
        print(' | '.join(line), flush=True)

    print()
    print('%-14s %10s %10s %12s %12s' % ('format', 'median kB', 'total kB', 'encode ms', 'decode ms'))
    for label, rows in totals.items():
        print('%-14s %10.1f %10.0f %12.2f %12.2f' % (
            label, statistics.median(r[0] for r in rows) / 1000, sum(r[0] for r in rows) / 1000,
            statistics.median(r[1] for r in rows), statistics.median(r[2] for r in rows)))


if __name__ == '__main__':
    main()
