"""pytest plugin: what a process holds after each test, in run order.

Prints GROWTH <seconds> <gc objects> <toplevel windows> <threads>
<GObject wrappers alive> <test> after every test's teardown.
"""
import gc
import threading
import time

_start = {}


def pytest_runtest_setup(item):
    _start[item.nodeid] = time.monotonic()


def pytest_runtest_logreport(report):
    if report.when != 'teardown' or report.nodeid not in _start:
        return
    took = time.monotonic() - _start.pop(report.nodeid)
    from gi.repository import GObject, Gtk
    objs = gc.get_objects()
    wrappers = sum(1 for o in objs if isinstance(o, GObject.Object))
    print('\nGROWTH %.3f %d %d %d %d %s' % (
        took, len(objs), len(Gtk.Window.list_toplevels()),
        threading.active_count(), wrappers, report.nodeid), flush=True)
