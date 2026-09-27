# Thumbnails of the 60 pages of big60.cbz at 128x128, as the thumbnail
# bar asks for them, without storing them on disk. Best of three passes.
import glob, os, sys, time
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else '/tmp/mcomix-git')
import gi
gi.require_version('Gdk', '4.0'); gi.require_version('Gtk', '4.0'); gi.require_version('GdkPixbuf', '2.0')
from mcomix import thumbnail_tools
pages = sorted(glob.glob(os.path.expanduser('~/.claude/skills/mcomix-loop/state/scratch/thumbbench/pages/*.jpg')))
best = None
for _ in range(3):
    t = time.perf_counter()
    for path in pages:
        assert thumbnail_tools.Thumbnailer(store_on_disk=False, size=(128, 128)).thumbnail(path) is not None
    took = time.perf_counter() - t
    best = took if best is None else min(best, took)
print(f'{len(pages)} thumbnails: {best*1000:.0f} ms, {best/len(pages)*1000:.1f} ms each')
sys.stdout.flush(); os._exit(0)
