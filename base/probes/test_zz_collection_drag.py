"""A real press and pull on collection rows of the library that are not
selected: what the drag offers.  Copy into test/ and run under xvfb-run
with -s; prints PROBE lines."""
import subprocess, time, unittest.mock
from gi.repository import Gdk, Graphene
from . import pump
from .test_library_dialog import _LibraryWindowTest
from mcomix import constants
from mcomix.library import collection_area
from mcomix.preferences import prefs

offered = []
_prep = collection_area._CollectionArea._drag_prepare
_new = Gdk.ContentProvider.new_for_value


def _p(self, source, x, y):
    with unittest.mock.patch.object(Gdk.ContentProvider, 'new_for_value', wraps=_new) as made:
        r = _prep(self, source, x, y)
    offered.append(made.call_args.args[0] if r is not None else None)
    return r


collection_area._CollectionArea._drag_prepare = _p


def settle(n=10):
    for _ in range(n):
        pump(); time.sleep(0.02)


def xdo(*args):
    subprocess.run(('xdotool',) + tuple(str(a) for a in args), check=True)


class Probe(_LibraryWindowTest):
    def test_real(self):
        prefs['last library collection'] = constants.COLLECTION_ALL
        dialog = self._open()
        ids = {name: dialog.backend.add_collection(name) for name in ('Alpha', 'Beta', 'Gamma')}
        area = dialog.collection_area
        area.display_collections(); dialog.present(); settle(30)
        lst = area._list
        ys = {}
        for y in range(2, 400, 4):
            row = lst.row_at(40, y)
            if row is not None and row.collection in ids.values():
                ys.setdefault(row.collection, []).append(y)
        mid = {c: sum(v) // len(v) for c, v in ys.items()}
        print('PROBE ids', ids, 'row middles', mid, 'selected', area.get_current_collection())
        ok, pt = lst.compute_point(dialog, Graphene.Point().init(0, 0))
        dx, dy = dialog.get_surface_transform()
        xid = dialog.get_surface().get_xid()

        def pull(collection, across=40):
            del offered[:]
            x, y = int(pt.x + dx + across), int(pt.y + dy + mid[collection])
            xdo('mousemove', '--window', xid, x, y); settle(4)
            xdo('mousedown', 1); settle(4)
            for i in range(1, 8):
                xdo('mousemove', '--window', xid, x + 5 * i, y + 3 * i); settle(3)
            xdo('mouseup', 1); settle()
            return [o for o in offered if o is not None][:1] or offered[:1]

        print('PROBE All books selected, pull from Beta (id %d): offers' % ids['Beta'], pull(ids['Beta']), 'selected after', area.get_current_collection())
        print('PROBE then pull from Gamma (id %d): offers' % ids['Gamma'], pull(ids['Gamma']), 'selected after', area.get_current_collection())
        print('PROBE pull from Alpha at its left edge (id %d): offers' % ids['Alpha'], pull(ids['Alpha'], across=4), 'selected after', area.get_current_collection())
