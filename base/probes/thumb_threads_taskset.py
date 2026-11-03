# Thumbnails of big60.cbz's pages (x4) at 128x128 with n threads, best of 3.
import glob, os, sys, time, resource
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.getcwd())
import gi
gi.require_version('Gdk', '4.0'); gi.require_version('Gtk', '4.0'); gi.require_version('GdkPixbuf', '2.0')
from mcomix import thumbnail_tools
pages = sorted(glob.glob(os.path.join(sys.argv[1], '*.' + os.environ.get('EXT','jpg')))) * 4
def one(path):
    assert thumbnail_tools.Thumbnailer(store_on_disk=False, size=(128, 128)).thumbnail(path) is not None
for n in [int(t) for t in sys.argv[2].split(',')]:
    best = None
    for _ in range(3):
        t = time.perf_counter()
        with ThreadPoolExecutor(n) as ex:
            list(ex.map(one, pages))
        took = time.perf_counter() - t
        best = took if best is None else min(best, took)
    print(f'{n:3d} threads: {best*1000:.0f} ms for {len(pages)}; maxrss {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024} MB', flush=True)
os._exit(0)
