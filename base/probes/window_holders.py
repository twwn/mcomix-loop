"""pytest plugin: at the end of the session, what keeps closed
MainWindows alive.  Prints the count and, for the oldest, what refers to
it: bound methods by qualname, instance dicts by their owner's class,
cells and closures by function, other containers by type."""
import gc
import types


def _describe(ref, others):
    if isinstance(ref, types.MethodType):
        return 'bound method %s' % ref.__func__.__qualname__
    if isinstance(ref, dict):
        for owner in gc.get_referrers(ref):
            if getattr(owner, '__dict__', None) is ref:
                return 'attribute of %s' % type(owner).__qualname__
        return 'dict (%d keys: %s)' % (len(ref), ', '.join(sorted(map(str, ref))[:6]))
    if isinstance(ref, types.CellType):
        for fn in gc.get_referrers(ref):
            if isinstance(fn, types.FunctionType):
                return 'closure cell of %s' % fn.__qualname__
        return 'cell'
    if isinstance(ref, types.FrameType):
        return 'frame %s' % ref.f_code.co_qualname
    return type(ref).__qualname__


def pytest_sessionfinish(session):
    gc.collect()
    from mcomix import main
    windows = [o for o in gc.get_objects() if isinstance(o, main.MainWindow)]
    print('\nHOLDERS: %d MainWindow alive' % len(windows))
    if not windows:
        return
    window = windows[0]
    seen = set()
    for ref in gc.get_referrers(window):
        if ref is windows:
            continue
        d = _describe(ref, windows)
        if d not in seen:
            seen.add(d)
            print('HOLDERS:', d)
