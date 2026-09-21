# Copy into <worktree>/test/test_zz_measure.py and run with
# timeout -k 5 120 env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -a python3 -m pytest test/test_zz_measure.py -q -p no:cacheprovider -s -k "M and (edit or library)" | grep -E "MEASURE|FINAL|SURV"
# Prefix MCOMIXPATH=/tmp/mcomix-git to measure master's code. Delete it afterwards.
import collections, gc, os
from .test_dialog_freed import MainWindowDialogsFreedTest as T
from . import pump

def rss():
    with open('/proc/self/statm') as f:
        return int(f.read().split()[1]) * os.sysconf('SC_PAGE_SIZE') // 1024

class M(T):
    def _cycle(self, name, n=20):
        for i in range(3):
            w = self._opened_by(self._ui_action(name)); w.close(); del w; pump()
        gc.collect(); before = rss()
        fin, allk = [], []
        for i in range(n):
            w = self._opened_by(self._ui_action(name))
            w.weak_ref(lambda: fin.append(1))
            stack = [w.get_child()]
            while stack:
                x = stack.pop()
                if x is None:
                    continue
                tn = type(x).__name__
                x.weak_ref(lambda tn=tn: fin.append(('d', tn)))
                allk.append(tn)
                ch = x.get_first_child()
                while ch is not None:
                    stack.append(ch); ch = ch.get_next_sibling()
            x = ch = stack = None
            w.close(); del w; pump()
        gc.collect(); pump(); gc.collect()
        # Some cells are finalized only when the frame clock next ticks.
        from . import wait_for
        wait_for(lambda: False, seconds=float(os.environ.get('SETTLE', '0')))
        gc.collect()
        made = collections.Counter(allk)
        gone = collections.Counter(t for f in fin if isinstance(f, tuple) for _k, t in [f])
        print('FINALIZED windows', fin.count(1), 'widgets', sum(gone.values()), 'of', len(allk))
        print('SURVIVORS', dict((made - gone).most_common(25)))
        print('MEASURE', name, os.environ.get('MCOMIXPATH', 'branch'), 'rss_delta_kib', rss() - before)

    def test_edit(self):
        self._cycle('edit_archive')

    def test_library(self):
        self._cycle('library')
