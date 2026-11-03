import os, subprocess, sys, time, unittest.mock
from gi.repository import Graphene, Gtk
from . import pump, wait_for
from .test_library_dialog import ReadingListTest
from mcomix.library import book_area

HELPER = os.environ['DRAG_HELPER']
_acc = book_area._BookArea._accepts_books
_drp = book_area._BookArea._books_dropped
_prep = book_area._BookArea._drag_prepare
def _a(self, target, drop):
    r = _acc(self, target, drop); print('PROBE accept', r, drop.get_drag(), drop.get_actions(), drop.get_formats().to_string(), flush=True); return r
def _d(self, target, value, x, y):
    r = _drp(self, target, value, x, y); print('PROBE dropped', repr(value), x, y, self._covers.position_at(x, y), r, flush=True); return r
def _p(self, source, x, y):
    r = _prep(self, source, x, y); print('PROBE prepare', r, flush=True); return r
book_area._BookArea._accepts_books = _a
book_area._BookArea._books_dropped = _d
book_area._BookArea._drag_prepare = _p
if os.environ.get('ACCEPT_ALL'):
    book_area._BookArea._accepts_books = lambda self, target, drop: True


def settle(n=25):
    for _ in range(n):
        pump(); time.sleep(0.02)


def point(widget, window):
    ok, pt = widget.compute_point(window, Graphene.Point().init(widget.get_width() / 2, widget.get_height() / 2))
    dx, dy = window.get_surface_transform()
    return int(pt.x + dx), int(pt.y + dy)


def xdo(*args):
    subprocess.run(('xdotool',) + tuple(str(a) for a in args), check=True)


class Probe(ReadingListTest):
    def _cell(self, position):
        return [c for c in self.area._covers._each_cell() if c.position == position and c.get_mapped()][0]

    def _drag(self, xid, start, end, start_xid=None):
        xdo('mousemove', '--window', start_xid or xid, *start); settle(5)
        xdo('mousedown', 1); settle(5)
        if start_xid:
            xdo('mousemove', '--window', start_xid, start[0] + 20, start[1] + 20); settle(5)
        for i in range(1, 11):
            if start_xid and i < 3:
                continue
            x = start[0] + (end[0] - start[0]) * i // 10 if not start_xid else end[0] - 10 + i
            y = start[1] + (end[1] - start[1]) * i // 10 if not start_xid else end[1] - 10 + i
            xdo('mousemove', '--window', xid, x, y); settle(3)
        settle(5); xdo('mouseup', 1); settle()

    def test_real_drags(self):
        self.dialog.present(); settle()
        self.assertTrue(wait_for(lambda: len([c for c in self.area._covers._each_cell() if c.get_mapped() and c.position >= 0]) >= 4))
        xid = self.dialog.get_surface().get_xid()
        print('PROBE dialog size', self.dialog.get_width(), self.dialog.get_height(), 'shown', self._shown())
        adj = self.area.get_vadjustment(); seen = []
        adj.connect('value-changed', lambda a: seen.append(round(a.get_value())))
        placed = []
        real = self.area._place_books
        # Bound at connect time through self._books_dropped -> self._place_books lookup, so this is seen.
        self.area._place_books = lambda books, beside: placed.append((list(books), beside)) or real(books, beside)
        if not os.environ.get('UNSELECTED'):
            self.area._covers.select_only(0); settle(5)
        self._drag(xid, point(self._cell(0), self.dialog), point(self._cell(2), self.dialog))
        print('PROBE in-app drag 0 onto 2: placed calls', placed, 'shown', self._shown(), 'kept', self._kept(), 'selected', self._selected(), 'scroll values', seen)
        focus = self.dialog.get_focus()
        child = focus.get_first_child() if focus is not None else None
        print('PROBE focus on', type(focus).__name__, getattr(child, 'position', None))

        added = []
        self.dialog.add_books = lambda paths, collection: added.append((list(paths), collection))
        helper = subprocess.Popen([sys.executable, '-I', HELPER, self.paths['1.zip']], stdout=subprocess.PIPE, text=True)
        try:
            line = helper.stdout.readline().split()
            print('PROBE helper', line)
            hxid = line[1]
            xdo('windowmove', hxid, 1900, 100); settle(10)
            before = len(placed)
            self._drag(xid, (100, 100), point(self._cell(1), self.dialog), start_xid=hxid)
            settle(20)
            print('PROBE file drop: add_books calls', added, 'place calls', placed[before:], 'shown', self._shown())
        finally:
            helper.kill(); helper.wait()
