import random, sys, collections
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else '.')
from mcomix import zoom, constants
M = constants.ZoomMode
rng = random.Random(1)
bad = collections.Counter(); shown = collections.Counter()
def report(kind, *info):
    bad[kind] += 1
    if shown[kind] < 2:
        shown[kind] += 1; print(kind, *info)
for _ in range(20000):
    n = rng.choice((1, 2))
    sizes = [[rng.randint(1, 4000), rng.randint(1, 4000)] for _ in range(n)]
    screen = [rng.randint(50, 3000), rng.randint(50, 3000)]
    mode = rng.choice((M.BEST, M.WIDTH, M.HEIGHT, M.SIZE))
    up = rng.random() < 0.5
    z = zoom.ZoomModel(); z.set_fit_mode(mode); z.set_scale_up(up)
    res, dist = z.get_zoomed_size(sizes, screen, constants.PageAxis.WIDTH, [False]*n, False, False)
    uw = sum(r[0] for r in res); uh = max(r[1] for r in res)
    tol = n + 1
    if mode in (M.BEST, M.WIDTH) and uw > screen[0] + tol and (up or sum(s[0] for s in sizes) > screen[0]):
        report('wider than screen', mode, up, sizes, screen, res)
    if mode in (M.BEST, M.HEIGHT) and uh > screen[1] + tol:
        report('taller than screen', mode, up, sizes, screen, res)
    for s, r in zip(sizes, res):
        if not up and (r[0] > s[0] or r[1] > s[1]):
            report('enlarged without scale up', mode, sizes, screen, res)
        # aspect ratio within one pixel of rounding
        if s[0] > 20 and s[1] > 20 and r[0] > 20 and r[1] > 20:
            if abs(r[0] / r[1] - s[0] / s[1]) > (s[0] / s[1]) * 0.06:
                report('aspect', mode, up, s, r, screen)
    if up and mode == M.BEST:
        if not (uw >= screen[0] - tol or uh >= screen[1] - tol):
            report('best fit leaves room on both axes', sizes, screen, res)
    if up and mode == M.WIDTH and abs(uw - screen[0]) > tol:
        report('fit width misses width', sizes, screen, res)
    if up and mode == M.HEIGHT and abs(uh - screen[1]) > tol:
        report('fit height misses height', sizes, screen, res)
print(dict(bad))
