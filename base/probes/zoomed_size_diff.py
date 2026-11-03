"""Compare ZoomModel.get_zoomed_size of the checkout with an older zoom.py.

Usage, from REPO: git show <rev>:mcomix/zoom.py > <old.py>;
PYTHONPATH=. timeout -k 5 60 python3 <this> <old.py> [cases]
Random pages (one to three, some fixed), screens, fit modes, scale-up, user zoom, both
distribution axes, prefer_same_size and fit_same_size; prints how many cases differ.
"""
import importlib.util
import random
import sys

from mcomix import constants
from mcomix import zoom as new

spec = importlib.util.spec_from_file_location('zoom_old', sys.argv[1])
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
cases = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
M = constants.ZoomMode
r = random.Random(2)
diff = 0
for _ in range(cases):
    n = r.randint(1, 3)
    sizes = [[r.randint(1, 4000), r.randint(1, 4000)] for _ in range(n)]
    screen = [r.randint(50, 3000), r.randint(50, 3000)]
    mode = r.choice((M.BEST, M.WIDTH, M.HEIGHT, M.SIZE, M.MANUAL))
    up = r.random() < .5
    axis = r.choice((constants.PageAxis.WIDTH, constants.PageAxis.HEIGHT))
    dnt = [r.random() < .15 for _ in range(n)]
    same, fit = r.random() < .6, r.random() < .6
    zoom_log = r.randint(-8, 8)
    out = []
    for mod in (new, old):
        z = mod.ZoomModel()
        z.set_fit_mode(mode)
        z.set_scale_up(up)
        z._user_zoom_log = zoom_log
        out.append(z.get_zoomed_size([list(s) for s in sizes], screen, axis, list(dnt), same, fit))
    diff += out[0] != out[1]
print(cases, 'cases, differing:', diff)
