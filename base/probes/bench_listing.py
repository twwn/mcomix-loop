"""Time OrderedFileProvider.list_files(IMAGES) over large folders.

Usage, from the checkout:
  timeout -k 5 60 python3 <this> <scratch dir>
Builds, once, <dir>/named (10,000 small JPEGs named page%05d.jpg) and
<dir>/bare (the same pictures without an extension), on whatever file
system <dir> is on, and prints the median of five listings of each.
"""
import os
import shutil
import statistics
import sys
import time

sys.path.insert(0, os.getcwd())
import gi  # noqa: E402
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from PIL import Image  # noqa: E402

from mcomix import file_provider  # noqa: E402

base = sys.argv[1]
COUNT = 10000
sample = os.path.join(base, 'sample.jpg')
if not os.path.exists(sample):
    os.makedirs(base, exist_ok=True)
    Image.new('RGB', (8, 8), (40, 80, 120)).save(sample)
for kind, suffix in (('named', '.jpg'), ('bare', '')):
    folder = os.path.join(base, kind)
    if not os.path.isdir(folder) or len(os.listdir(folder)) != COUNT:
        os.makedirs(folder, exist_ok=True)
        for index in range(COUNT):
            shutil.copyfile(sample, os.path.join(folder, 'page%05d%s' % (index, suffix)))
    provider = file_provider.OrderedFileProvider(os.path.join(folder, os.listdir(folder)[0]))
    provider.list_files(file_provider.FileProvider.IMAGES)
    times = []
    for _ in range(5):
        start = time.perf_counter()
        listed = provider.list_files(file_provider.FileProvider.IMAGES)
        times.append(time.perf_counter() - start)
    print('%s: %d listed, median %.1f ms (min %.1f)' % (kind, len(listed), statistics.median(times) * 1e3, min(times) * 1e3), flush=True)
