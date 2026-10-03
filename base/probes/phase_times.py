"""pytest plugin: total time spent in chosen calls over a run, printed at
the end as PHASE <name> <seconds> <calls>.  Wraps MainWindow.__init__,
terminate_program, destroy and _release (where it exists),
widgets.release, MComixTest.tearDown and gc.collect."""
import collections
import gc
import time

_t = collections.defaultdict(float)
_n = collections.Counter()


def _wrap(owner, name, label):
    orig = getattr(owner, name, None)
    if orig is None:
        return

    def timed(*a, **k):
        t = time.perf_counter()
        try:
            return orig(*a, **k)
        finally:
            _t[label] += time.perf_counter() - t
            _n[label] += 1
    setattr(owner, name, timed)


def pytest_configure(config):
    from mcomix import main, widgets
    import test
    for name in ('__init__', 'terminate_program', 'destroy', '_release'):
        _wrap(main.MainWindow, name, 'MainWindow.' + name)
    _wrap(widgets, 'release', 'widgets.release')
    _wrap(test.MComixTest, 'tearDown', 'MComixTest.tearDown')
    _wrap(gc, 'collect', 'gc.collect')


def pytest_sessionfinish(session):
    for k in sorted(_t):
        print('\nPHASE %-28s %7.3f %5d' % (k, _t[k], _n[k]), end='')
    print()
