"""Time is_later_part over a folder of 3000 parts of 1000 books: as it was
just written, with the wait for the tick, and with the tick off (the old way)."""
import os, shutil, sys, tempfile, time
from test.test_kfx import split_book, picture
from mcomix.archive import kfx

root = tempfile.mkdtemp(dir=sys.argv[1])
try:
    folder = os.path.join(root, 'apps')
    os.mkdir(folder)
    for n in range(int(sys.argv[2])):
        parts = split_book([picture()], main=f'CR!M{n}', metadata=f'CR!D{n}', resources=f'CR!R{n}')
        for name, data in zip((f'CR!M{n}', f'CR!D{n}', f'CR!R{n}'), parts):
            with open(os.path.join(folder, name + '.kfx'), 'wb') as fp:
                fp.write(data)
    paths = [os.path.join(folder, n) for n in os.listdir(folder)]
    def sweep():
        start = time.perf_counter()
        later = sum(kfx.is_later_part(p) for p in paths)
        return time.perf_counter() - start, later
    for p in paths:  # the summaries of every part, as the first listing leaves them
        kfx._summary(p)
    now = time.time_ns()
    os.utime(folder, ns=(now, now))
    print('folder just changed, tick 2 s: %.3f s, %d later' % sweep(), flush=True)
    now = time.time_ns()
    os.utime(folder, ns=(now, now))
    tick, kfx._FOLDER_TIME_TICK_NS = kfx._FOLDER_TIME_TICK_NS, 0
    print('folder just changed, no tick (the old way): %.3f s, %d later' % sweep(), flush=True)
    kfx._FOLDER_TIME_TICK_NS = tick
    old = time.time_ns() - 3_600_000_000_000
    os.utime(folder, ns=(old, old))
    print('folder an hour old, first: %.3f s, %d later' % sweep(), flush=True)
    print('folder an hour old, again: %.3f s, %d later' % sweep(), flush=True)
finally:
    shutil.rmtree(root)
    sys.stdout.flush()
    os._exit(0)
