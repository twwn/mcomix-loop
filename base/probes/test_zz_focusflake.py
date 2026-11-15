import os
from gi.repository import Gdk, Gtk
from . import pump, keep_focus_within
from .test_column_list import ColumnListViewTest as _Base

LOG = os.environ.get('FLAKE_LOG', '/dev/null')


def _name(widget):
    return 'None' if widget is None else '%s%s' % (
        type(widget).__name__, ':' + widget.row.name if getattr(widget, 'row', None) else '')


class _Probe(_Base):
    def test_probe(self):
        self.view.set_search_attribute('name')
        got = self.view.grab_focus()
        first = _name(self.window.get_focus())
        self.view.select_and_focus(0)
        self._settle()
        second = _name(self.window.get_focus())
        if os.environ.get('FLAKE_FORCE'):
            widget = self.window.get_focus()
            while widget is not None:
                widget.unset_state_flags(Gtk.StateFlags.FOCUS_WITHIN)
                widget = widget.get_parent()
        if os.environ.get('FLAKE_FIX'):
            keep_focus_within(self.window)
        self.view._search_typed(None, ord('t'), 0, Gdk.ModifierType(0))
        self.view._search_typed(None, ord('h'), 0, Gdk.ModifierType(0))
        self._settle()
        third = _name(self.window.get_focus())
        with open(LOG, 'a') as log:
            log.write('%s active %s within %s child %s third %s\n' % (
                'PASS' if self._focused() == 'three' else 'FAIL',
                self.window.is_active(),
                bool(self.view.get_state_flags() & Gtk.StateFlags.FOCUS_WITHIN),
                _name(self.view.get_focus_child()), third))
        self.assertEqual(self._focused(), 'three')


for _i in range(48):
    globals()['Probe%02d' % _i] = type('Probe%02d' % _i, (_Probe,), {})
del _Base
