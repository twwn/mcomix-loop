import subprocess, time
from unittest import mock
from .test_pageselect import PageselectTest as _Base
from . import pump


def spin(n):
    for _ in range(n):
        pump(); time.sleep(0.02)


class Probe(_Base):
    def _real(self, typed):
        seen = []
        self.dialog.connect('response', lambda d, r: seen.append(r))
        with mock.patch.object(self.window, 'set_page') as set_page:
            spin(20)
            xid = self.dialog.get_surface().get_xid()
            subprocess.run(['xdotool', 'windowactivate', '--sync', str(xid)])
            subprocess.run(['xdotool', 'windowfocus', '--sync', str(xid)])
            spin(10)
            subprocess.run(['xdotool', 'type', '--delay', '30', typed], check=True)
            spin(20)
            subprocess.run(['xdotool', 'key', 'Return'], check=True)
            spin(40)
            print('RESULT', typed, seen, set_page.call_args_list, flush=True)

    def test_a(self):
        self._real('3')

    def test_b(self):
        self._real('99')
