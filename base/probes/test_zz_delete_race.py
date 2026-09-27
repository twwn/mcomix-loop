"""96 copies of the test that lost a race with FileHandler.thread_delete().

The deletion thread is slowed down, at a random point, so that it is
still removing the book's temporary directory while MComixTest removes
the test's.
"""
import os
import random
import shutil
import tempfile
import threading
import time
import types
from unittest import mock

from test.test_file_handler import BusyCursorTest as _Base


_filled = threading.Event()


def _slow_rmtree(path, ignore_errors=False):
    # Fill the book's directory, wait until MComixTest._restore() has
    # started (it puts tempfile.tempdir back first), then delete alongside.
    for i in range(20000):
        open(os.path.join(path, '%04d' % i), 'w').close()
    _filled.set()
    own = tempfile.tempdir
    deadline = time.monotonic() + 5
    while tempfile.tempdir == own and time.monotonic() < deadline:
        time.sleep(0.0005)
    shutil.rmtree(path, True)


class _Probe(_Base):

    def setUp(self):
        super().setUp()
        from mcomix import file_handler
        slow = types.SimpleNamespace(rmtree=_slow_rmtree)
        patcher = mock.patch.object(file_handler, 'shutil', slow)
        _filled.clear()
        patcher.start()
        self.addCleanup(_filled.wait, 5)
        self.addCleanup(patcher.stop)


for _name in [n for n in dir(_Base) if n.startswith('test_')]:
    if _name != 'test_closing_while_a_listing_runs_clears_the_wait_cursor':
        setattr(_Probe, _name, None)

for _i in range(16):
    globals()['Probe%d' % _i] = type('Probe%d' % _i, (_Probe,), {})
del _Base
