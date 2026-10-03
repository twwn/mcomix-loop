"""pytest plugin: time chosen MainWindow calls per test, in run order.
Prints CALLS <test index> <name> <seconds> for each timed call."""
import time

_n = [0]


def pytest_configure(config):
    from mcomix import main
    for name in ('set_visible', 'present', 'set_child', 'restore_window_geometry',
                 'write_config_files', 'set_default_size'):
        orig = getattr(main.MainWindow, name)

        def timed(self, *a, _orig=orig, _name=name, **k):
            t = time.perf_counter()
            try:
                return _orig(self, *a, **k)
            finally:
                print('CALLS %d %s %.5f' % (_n[0], _name, time.perf_counter() - t), flush=True)
        setattr(main.MainWindow, name, timed)


def pytest_runtest_teardown(item, nextitem):
    _n[0] += 1
