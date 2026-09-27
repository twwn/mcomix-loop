"""Time image_tools.get_most_common_edge_colour() on real pages.

Usage: timeout -k 5 60 xvfb-run -a python3 bench_edge_colour.py <mcomix tree> <image>...
Prints the median of 30 calls per image, one and two pages, in ms.
"""
import statistics
import sys
import time

sys.path.insert(0, sys.argv[1])
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from PIL import Image
from mcomix import image_tools

pixbufs = [image_tools.pil_to_pixbuf(Image.open(path).convert('RGB')) for path in sys.argv[2:]]
for label, arg in (('one page', pixbufs[0]), ('two pages', (pixbufs[0], pixbufs[-1]))):
    times = []
    for _ in range(30):
        start = time.perf_counter()
        answer = image_tools.get_most_common_edge_colour(arg)
        times.append(time.perf_counter() - start)
    print('%s: %.2f ms  %s' % (label, statistics.median(times) * 1000,
                               [round(c * 255) for c in answer[:3]]))
