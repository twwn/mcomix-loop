"""Compare ZoomModel._scale_distributed of the checkout with an older zoom.py.

Usage, from REPO: git show <rev>:mcomix/zoom.py > <old.py>;
PYTHONPATH=. timeout -k 5 60 python3 <this> <old.py> [cases]
Prints how many random cases give different scales; 0 for a pure refactor.
"""
import importlib.util
import random
import sys

from mcomix import zoom as new

spec = importlib.util.spec_from_file_location('zoom_old', sys.argv[1])
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
cases = int(sys.argv[2]) if len(sys.argv) > 2 else 200000
r = random.Random(1)
diff = 0
for _ in range(cases):
    n = r.randint(0, 6)
    axis = r.randint(0, 1)
    sizes = [[r.choice([r.randint(1, 40), r.randint(1, 3000)]) for _ in range(2)] for _ in range(n)]
    if r.random() < .3 and n > 1:
        sizes[1] = list(sizes[0])
    dnt = [r.random() < .2 for _ in range(n)]
    m = r.randint(1, 4000)
    up = r.random() < .5
    diff += new.ZoomModel._scale_distributed(sizes, axis, m, up, dnt) != old.ZoomModel._scale_distributed(sizes, axis, m, up, dnt)
print(cases, 'cases, differing:', diff)
