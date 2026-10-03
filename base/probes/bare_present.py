"""Does presenting a fresh Gtk.Window get slower the more windows the
process has presented and destroyed?  No MComix; RENDERER and KIND pick
the variant.  Prints the mean present() time per quarter of N windows."""
import gc
import os
import time

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gtk  # noqa: E402

N = int(os.environ.get('N', '200'))
ctx = GLib.MainContext.default()
times = []
for i in range(N):
    w = Gtk.Window()
    w.set_child(Gtk.Label(label='x'))
    t = time.perf_counter()
    w.present()
    times.append(time.perf_counter() - t)
    for _ in range(50):
        ctx.iteration(False)
    w.destroy()
    for _ in range(50):
        ctx.iteration(False)
    del w
    gc.collect()
q = N // 4
print('present', ' '.join('%.4f' % (sum(times[k*q:(k+1)*q]) / q) for k in range(4)), flush=True)
os._exit(0)
