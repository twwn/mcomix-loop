"""What keeps a closed MainWindow alive: the objects held from outside
Python (their reference count exceeds what Python refers to them from)
on the way from the window back through its referrers.  Built on
MComixTest; ROOT=<checkout> picks the tree (default: the working directory).
Run under xvfb-run with a timeout; prints ROOT lines to stderr.
"""
import gc
import os
import sys
import types
import unittest
import weakref

sys.path.insert(0, os.environ.get('ROOT') or os.getcwd())   # the checkout this runs from, or ROOT

from test import MComixTest, get_testfile_path, pump, wait_for  # noqa: E402

from mcomix import constants, icons, keybindings, main  # noqa: E402

DEPTH = int(os.environ.get('DEPTH', '6'))


def describe(o):
    if isinstance(o, types.MethodType):
        return 'bound %s' % o.__func__.__qualname__
    if isinstance(o, types.FunctionType):
        return 'function %s' % o.__qualname__
    if isinstance(o, dict):
        for owner in gc.get_referrers(o):
            if getattr(owner, '__dict__', None) is o:
                return '__dict__ of %s' % type(owner).__qualname__
        return 'dict keys %s' % sorted(map(str, o))[:5]
    if isinstance(o, types.CellType):
        for t in gc.get_referrers(o):
            for f in gc.get_referrers(t):
                if isinstance(f, types.FunctionType):
                    return 'cell of %s' % f.__qualname__
        return 'cell'
    if isinstance(o, types.ModuleType):
        return 'module %s' % o.__name__
    return type(o).__qualname__


class Probe(MComixTest):

    def test_probe(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        keybindings._manager = None
        window = main.MainWindow(open_path=get_testfile_path(
            'archives', '01-ZIP-Normal.zip'))
        main.set_main_window(window)
        wait_for(lambda: window.imagehandler.get_number_of_pages() > 0,
                 seconds=20)
        pump()
        ref = weakref.ref(window)
        window.terminate_program()
        window.destroy()
        main.set_main_window(None)
        del window
        pump()
        gc.collect()
        pump()
        gc.collect()
        target = ref()
        out = open(os.environ.get('OUT', '/dev/stderr'), 'a', buffering=1)
        if target is None:
            print('ROOT window freed', file=out, flush=True)
            return
        seen = {id(target)}
        layer = [target]
        printed = set()
        for depth in range(DEPTH):
            nxt = []
            for o in layer:
                for r in gc.get_referrers(o):
                    if id(r) in seen or isinstance(r, types.FrameType) \
                            or r is layer or r is nxt:
                        continue
                    seen.add(id(r))
                    nxt.append(r)
                    held = sys.getrefcount(r) - 2 - len(gc.get_referrers(r))
                    gref = getattr(r, '__grefcount__', None)
                    if held > 0 or (gref is not None and gref > 1) \
                            or isinstance(r, types.ModuleType):
                        d = '%d %s (py-extra %d, gref %s) <- %s' % (
                            depth, describe(r), held, gref, describe(o))
                        if d not in printed:
                            printed.add(d)
                            print('ROOT', d, file=out)
            layer = nxt
        out.flush()


if __name__ == '__main__':
    unittest.main(argv=['x'], exit=False)
    sys.stdout.flush()
    os._exit(0)
