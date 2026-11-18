"""PSNR of each lossy format against the 500 px cover, at 500 and at the
drawn sizes 250 and 125 (both scaled down with LANCZOS from the decoded
picture, as the sized cover is)."""
import io
import math
import os
import sys

from PIL import Image, ImageChops, ImageStat
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench_cover_formats as b  # noqa: E402  (runs nothing at import: guarded below)


def psnr(a, c):
    diff = ImageChops.difference(a, c)
    mse = sum(v * v for v in ImageStat.Stat(diff).rms) / 3
    return 99.0 if mse == 0 else 20 * math.log10(255 / math.sqrt(mse))


def scaled(img, box):
    img = img.copy()
    img.thumbnail((box, box), Image.Resampling.LANCZOS)
    return img


FORMATS = [('webp-q90', 'WEBP', {'quality': 90, 'method': 4}),
           ('webp-q80', 'WEBP', {'quality': 80, 'method': 4}),
           ('avif-q90', 'AVIF', {'quality': 90}),
           ('avif-q75', 'AVIF', {'quality': 75}),
           ('jpeg-q90', 'JPEG', {'quality': 90})]
rows = {}
for name, img in b.covers():
    cover = b.fit(img)
    line = ['%-24s' % name]
    for label, fmt, options in FORMATS:
        data = io.BytesIO()
        cover.save(data, fmt, **options)
        back = Image.open(io.BytesIO(data.getvalue())).convert('RGB')
        values = [psnr(cover, back)] + [psnr(scaled(cover, s), scaled(back, s)) for s in (250, 125)]
        rows.setdefault(label, []).append(values)
        line.append('%s %.1f/%.1f/%.1f dB' % (label, *values))
    print(' | '.join(line), flush=True)
print('\nmedian PSNR (dB) at 500 / 250 / 125:')
for label, values in rows.items():
    print('%-10s %s' % (label, ' / '.join('%.1f' % sorted(v[i] for v in values)[len(values) // 2] for i in range(3))))
print('lowest at 500: %s' % ', '.join('%s %.1f' % (l, min(v[0] for v in vs)) for l, vs in rows.items()))
