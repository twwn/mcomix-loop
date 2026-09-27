import sys, time
sys.path.insert(0, '.')
from test import MComixTest  # noqa: redirects constants
from mcomix import callback, image_handler
from mcomix.preferences import prefs
class FH:
    archive_type = None; file_loaded = False
    @callback.Callback
    def file_available(self, p): pass
    def ask_for_files(self, files): pass
class W:
    filehandler = FH()
    def displayed_double(self): return False
t = MComixTest('run'); t.setUp()
h = image_handler.ImageHandler(W())
for n in (200, 2000, 10000):
    h.set_image_files(['%05d.png' % i for i in range(n)])
    t0 = time.perf_counter()
    for page in range(1, 101): h._ask_for_pages(page * n // 101 + 1)
    print(n, 'pages: %.3f ms per turn' % ((time.perf_counter() - t0) * 10))
h.cleanup(); t.tearDown()
import os; sys.stdout.flush(); os._exit(0)
