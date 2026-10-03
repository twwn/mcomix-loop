# Thumbnails of the 60 pages of big60.cbz at 128x128, as the thumbnail
# bar asks for them, without storing them on disk. Best of three passes.
# Usage: python3 bench_thumb_bar.py [<mcomix tree>]  (default: the working
# directory). The pages are unpacked once into STATE/scratch/thumbbench/pages.
import glob, os, sys, time, zipfile
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
import gi
gi.require_version('Gdk', '4.0'); gi.require_version('Gtk', '4.0'); gi.require_version('GdkPixbuf', '2.0')
from mcomix import thumbnail_tools
HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(os.path.dirname(HERE), 'scratch', 'thumbbench', 'pages')
if not glob.glob(os.path.join(PAGES, '*.jpg')):
    zipfile.ZipFile(os.path.join(HERE, 'big60.cbz')).extractall(PAGES)
pages = sorted(glob.glob(os.path.join(PAGES, '*.jpg')))
best = None
for _ in range(3):
    t = time.perf_counter()
    for path in pages:
        assert thumbnail_tools.Thumbnailer(store_on_disk=False, size=(128, 128)).thumbnail(path) is not None
    took = time.perf_counter() - t
    best = took if best is None else min(best, took)
print(f'{len(pages)} thumbnails: {best*1000:.0f} ms, {best/len(pages)*1000:.1f} ms each')
sys.stdout.flush(); os._exit(0)
