"""Time what get_file_number() costs for a book among 2000 siblings.

Usage, from the checkout, under the gate's xvfb-run:
  timeout -k 5 60 python3 <this> <scratch dir>
Builds, once, <dir>/books with 2000 empty-ish ZIPs named vol%04d.cbz,
then prints the median of seven of each: the listing alone
(list_files(ARCHIVES)), the is_later_volume() filter over it, and the two
together as get_file_number() runs them. The first round is reported on
its own: is_later_volume() caches by (mtime, size), so it is the cold one.
"""
import os
import statistics
import sys
import time
import zipfile

sys.path.insert(0, os.getcwd())
import gi  # noqa: E402
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')

from mcomix import archive_tools, file_provider  # noqa: E402

base = os.path.join(sys.argv[1], 'books')
COUNT = 2000
if not os.path.isdir(base) or len(os.listdir(base)) != COUNT:
    os.makedirs(base, exist_ok=True)
    for number in range(COUNT):
        with zipfile.ZipFile(os.path.join(base, 'vol%04d.cbz' % number),
                             'w') as archive:
            archive.writestr('01.txt', 'x')
current = os.path.join(base, 'vol1000.cbz')


def one_round():
    provider = file_provider.get_file_provider([current])
    t0 = time.perf_counter()
    listed = provider.list_files(file_provider.FileProvider.ARCHIVES)
    t1 = time.perf_counter()
    kept = [path for path in listed
            if path == current or not archive_tools.is_later_volume(path)]
    t2 = time.perf_counter()
    assert len(kept) == COUNT, len(kept)
    return (t1 - t0) * 1000, (t2 - t1) * 1000


cold = one_round()
rounds = [one_round() for _ in range(7)]
print('cold: listing %.1f ms, filter %.1f ms' % cold)
print('warm median: listing %.1f ms, filter %.1f ms, total %.1f ms' % (
    statistics.median(r[0] for r in rounds),
    statistics.median(r[1] for r in rounds),
    statistics.median(r[0] + r[1] for r in rounds)))
sys.stdout.flush()
os._exit(0)
