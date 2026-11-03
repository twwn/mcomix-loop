import os, subprocess, time
from gi.repository import Gdk, Graphene
from . import pump, wait_for
from .test_library_dialog import ReadingListTest


def settle(n=15):
    for _ in range(n):
        pump(); time.sleep(0.02)


def xdo(*args):
    subprocess.run(('xdotool',) + tuple(str(a) for a in args), check=True)


class Probe(ReadingListTest):
    def _point(self, cell):
        ok, pt = cell.compute_point(self.dialog, Graphene.Point().init(cell.get_width() / 2, cell.get_height() / 2))
        dx, dy = self.dialog.get_surface_transform()
        return int(pt.x + dx), int(pt.y + dy)

    def _visible_cells(self):
        return sorted((c for c in self.area._covers._each_cell()
                       if c.get_mapped() and c.position >= 0
                       and 80 < c.compute_bounds(self.dialog)[1].get_y() < 380),
                      key=lambda c: c.position)

    def test_scroll(self):
        with self.backend.transaction():
            for i in range(300):
                self.backend._con.execute(
                    'insert into book (name, path, pages, format, size) values (?, ?, 20, 1, 1)',
                    ('x%d' % i, os.path.abspath('/nowhere/x%03d.cbz' % i)))
            self.backend._con.execute('insert or ignore into contain (collection, book) select ?, id from book', (self.list,))
        self.backend.set_collection_order(self.list, self.backend.get_collection_order(self.list))
        self._show(self.list)
        self.dialog.present(); settle(30)
        adj = self.area.get_vadjustment()
        adj.set_value(adj.get_upper() / 2); settle(30)
        xid = self.dialog.get_surface().get_xid()
        seen = []
        adj.connect('value-changed', lambda a: seen.append(round(a.get_value())))
        cells = self._visible_cells()
        first, target = cells[0], cells[-1]
        print('PROBE scrolled to', round(adj.get_value()), 'of', round(adj.get_upper()), 'cells', first.position, target.position)
        # A real click gives the cell the focus, then Alt+Right through the handler.
        xdo('mousemove', '--window', xid, *self._point(first)); settle(3)
        xdo('click', 1); settle()
        del seen[:]
        before = adj.get_value(); uid = self.area.get_book_at_path(first.position)
        moved = self.area._key_press(None, Gdk.KEY_Right, 0, Gdk.ModifierType.ALT_MASK); settle(30)
        print('PROBE alt+right moved', moved, 'value before %.0f after %.0f seen %s' % (before, adj.get_value(), seen), 'book now at', self.area.shown_ids().index(uid), 'was', first.position)
        # A real drag of that cover onto the last visible one.
        del seen[:]
        before = adj.get_value()
        cells = self._visible_cells(); first, target = cells[0], cells[-1]
        uid = self.area.get_book_at_path(first.position); was = first.position; goal = target.position
        x, y = self._point(first); tx, ty = self._point(target)
        xdo('mousemove', '--window', xid, x, y); settle(3)
        xdo('mousedown', 1); settle(5)
        for i in range(1, 11):
            xdo('mousemove', '--window', xid, x + (tx - x) * i // 10, y + (ty - y) * i // 10); settle(2)
        settle(5); xdo('mouseup', 1); settle(30)
        print('PROBE drag %d onto %d: book now at %d, value before %.0f after %.0f seen %s' % (was, goal, self.area.shown_ids().index(uid), before, adj.get_value(), seen))
