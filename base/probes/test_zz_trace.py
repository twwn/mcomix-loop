# Copy into <worktree>/test/test_zz_trace.py; set TRACE_ACTION (a win.* action
# name, e.g. library) and TRACE_CLASS (a type name that should be gone after
# the window closes). Prints how many survive and the referrer chain of one.
# timeout -k 5 60 env -u WAYLAND_DISPLAY GDK_BACKEND=x11 TRACE_ACTION=library TRACE_CLASS=_BookArea xvfb-run -a python3 -m pytest test/test_zz_trace.py -q -p no:cacheprovider -s -k Trace | grep -E "ALIVE|TRACE"
import gc, os, types
from .test_dialog_freed import MainWindowDialogsFreedTest as _Base
from . import pump

def desc(o):
    if isinstance(o, types.FunctionType): return 'fn ' + o.__qualname__
    if isinstance(o, types.MethodType): return 'bound ' + o.__func__.__qualname__
    if isinstance(o, types.CellType): return 'cell'
    if isinstance(o, dict): return 'dict keys=%s' % list(o)[:8]
    if isinstance(o, (list, tuple, set)): return '%s len %d' % (type(o).__name__, len(o))
    return type(o).__name__ + (' g%d' % o.__grefcount__ if hasattr(o, '__grefcount__') else '')

class Trace(_Base):
    def test_trace(self):
        w = self._opened_by(self._ui_action(os.environ['TRACE_ACTION'])); w.close(); del w
        pump(); gc.collect(); pump(); gc.collect()
        objs = [o for o in gc.get_objects() if type(o).__name__ == os.environ['TRACE_CLASS']]
        print('ALIVE', len(objs), [desc(o) for o in objs])
        mine, seen = set(), set()
        def walk(o, depth):
            if depth > 7: return
            refs = gc.get_referrers(o); mine.add(id(refs))
            for r in refs:
                if isinstance(r, types.FrameType) or id(r) in mine or r is objs or id(r) in seen: continue
                if type(r).__name__.endswith('iterator'): continue
                seen.add(id(r))
                print('TRACE' + '  ' * depth + desc(r))
                walk(r, depth + 1)
        if objs:
            walk(objs[0], 0)
