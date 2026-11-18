import io, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench_cover_formats as b  # noqa: E402
from cover_quality import psnr  # noqa: E402
from PIL import Image, AvifImagePlugin  # noqa: E402
AvifImagePlugin.DEFAULT_MAX_THREADS = 1
BOX = int(os.environ.get('BOX', '1000'))
FORMATS = [('png6', 'PNG', {'compress_level': 6}),
           ('webp-q90', 'WEBP', {'quality': 90, 'method': 4}),
           ('avif-q75-444', 'AVIF', {'quality': 75, 'subsampling': '4:4:4', 'max_threads': 1}),
           ('avif-q75-444-s8', 'AVIF', {'quality': 75, 'subsampling': '4:4:4', 'speed': 8, 'max_threads': 1})]
rows = {}
for name, img in b.covers():
    cover = img.convert('RGB').copy(); cover.thumbnail((BOX, BOX), Image.Resampling.LANCZOS)
    if max(cover.size) < BOX * 0.9:
        continue
    for label, fmt, options in FORMATS:
        data = io.BytesIO()
        enc = b.timed(lambda: cover.save(io.BytesIO(), fmt, **options))
        cover.save(data, fmt, **options); raw = data.getvalue()
        dec = b.timed(lambda: Image.open(io.BytesIO(raw)).load())
        back = Image.open(io.BytesIO(raw)).convert('RGB')
        rows.setdefault(label, []).append((len(raw), enc, dec, psnr(cover, back)))
print('box', BOX, 'covers', len(next(iter(rows.values()))))
print('%-16s %8s %8s %8s %12s' % ('format', 'kB med', 'enc ms', 'dec ms', 'PSNR med/min'))
for label, r in rows.items():
    print('%-16s %8.1f %8.1f %8.2f %6.1f/%.1f' % (label, statistics.median(x[0] for x in r) / 1000, statistics.median(x[1] for x in r), statistics.median(x[2] for x in r), statistics.median(x[3] for x in r), min(x[3] for x in r)))
