"""16 copies of the test that lost a race with a file chooser's preview.

The preview's thread fills the folder it unpacked a book into, waits until
MComixTest._restore() has started (it puts tempfile.tempdir back first), and
removes the folder alongside the test's own removal.  Python 3.12 only: from
3.13 on rmtree ignores an entry that vanished.

Run from the checkout, with the floors venv:
PYTHONPATH=. env -u WAYLAND_DISPLAY GDK_BACKEND=x11 timeout -k 5 280 xvfb-run -d \
    STATE/scratch/floorsenv/bin/python -m pytest -c test/pytest.ini --rootdir=. \
    STATE/probes/test_zz_preview_race.py -q -p no:warnings

With PROBE_BEFORE=1 the harness waits only for the threads it waited for
before e6783a20, which is how to watch the race lose.
"""
import os
import shutil
import tempfile
import threading
import time
import types
from unittest import mock

import test as harness
from test.test_dialog_freed import MainWindowDialogsFreedTest as _Base


_filled = threading.Event()


def _slow_rmtree(path, ignore_errors=False):
    for i in range(20000):
        open(os.path.join(path, '%05d' % i), 'w').close()
    own = tempfile.tempdir
    _filled.set()
    deadline = time.monotonic() + 15
    while tempfile.tempdir == own and time.monotonic() < deadline:
        time.sleep(0.0005)
    shutil.rmtree(path, True)


def _old_wait():
    for thread in threading.enumerate():
        if thread.name.endswith('-delete'):
            thread.join(10)


if os.environ.get('PROBE_BEFORE'):
    mock.patch.object(harness, 'wait_for_deletions', _old_wait).start()


class _Probe(_Base):

    def setUp(self):
        super().setUp()
        from mcomix import file_chooser_base_dialog
        patcher = mock.patch.object(file_chooser_base_dialog, 'shutil',
                                    types.SimpleNamespace(rmtree=_slow_rmtree))
        patcher.start()
        _filled.clear()
        # Cleanups run last added first: the test lets the preview go, this
        # sees it has filled its folder, and only then does _restore() run.
        self.addCleanup(patcher.stop)
        self.addCleanup(_filled.wait, 20)

    def test_a_file_chooser_closed_while_a_file_is_looked_into(self):
        # The book the CI's chooser happened to be previewing, asked for
        # outright: only a book makes a folder.
        from mcomix import file_chooser_base_dialog
        self._freed_while_previewing(
            harness.get_testfile_path('archives', '01-ZIP-Normal.zip'),
            file_chooser_base_dialog, 'file_details')


for _name in [n for n in dir(_Base) if n.startswith('test_')]:
    if _name != 'test_a_file_chooser_closed_while_a_file_is_looked_into':
        setattr(_Probe, _name, None)

for _i in range(16):
    globals()['Probe%d' % _i] = type('Probe%d' % _i, (_Probe,), {})
del _Base
