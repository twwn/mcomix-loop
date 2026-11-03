"""Before each of the suite's collections, name every Gtk.Window wrapper
and touch its child and title bar, one line-buffered line each: the line
before a crash names the window whose parts are gone. PROBE_OUT names the
file, in Windows spelling under Wine (Z:\\...)."""
import gc
import os

import test as T
from gi.repository import Gtk

_out = open(os.environ['PROBE_OUT'], 'w', buffering=1)
_orig = T._collect_garbage_now_and_then


def _probe():
    _out.write('PROBE %d\n' % T._tests_since_collecting)
    if T._tests_since_collecting + 1 >= T._COLLECT_EVERY:
        for o in gc.get_objects():
            if isinstance(o, Gtk.Window):
                _out.write('WIN %s refs=%d\n' % (type(o).__name__, o.__grefcount__))
                c = o.get_child()
                _out.write('  child %s\n' % type(c).__name__)
                t = o.get_titlebar()
                _out.write('  titlebar %s\n' % type(t).__name__)
                w = o.get_first_child()
                while w is not None:
                    _out.write('  part %s\n' % type(w).__name__)
                    w = w.get_next_sibling()
                _out.write('  default...\n')
                d = o.get_default_widget()
                _out.write('  default %s\n' % type(d).__name__)
                f = o.get_focus()
                _out.write('  focus %s\n' % type(f).__name__)
                _out.write('  dispose...\n')
                o.run_dispose()
                _out.write('  disposed\n')
    _orig()
    _out.write('COLLECTED\n')


T._collect_garbage_now_and_then = _probe
