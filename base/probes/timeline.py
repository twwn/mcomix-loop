"""Print each test's call time, in the order the tests ran."""
import time

_start = {}


def pytest_runtest_setup(item):
    _start[item.nodeid] = time.monotonic()


def pytest_runtest_logreport(report):
    if report.when == 'teardown' and report.nodeid in _start:
        print('\nTIMELINE %.2f %s' % (time.monotonic() - _start.pop(report.nodeid), report.nodeid), flush=True)
