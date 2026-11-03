import subprocess, time
from gi.repository import Gtk, Graphene
from .test_preferences_dialog import PreferencesDialogTest as _Base
from . import pump
from mcomix import column_list


def spin(n):
    for _ in range(n):
        pump(); time.sleep(0.02)


class Probe(_Base):
    def test_a(self):
        dialog = self._open()
        nb = dialog.notebook
        nb.set_current_page(nb.page_num(dialog.shortcuts))
        spin(10)
        for v in [w for w in [dialog.shortcuts.get_child()] if w]:
            pass
        from mcomix.column_list import ColumnListView
        def findv(w):
            if isinstance(w, ColumnListView): return w
            c = w.get_first_child()
            while c is not None:
                r = findv(c)
                if r: return r
                c = c.get_next_sibling()
        findv(dialog.shortcuts).expand_all()
        spin(30)
        cells = []
        def walk(w):
            c = w.get_first_child()
            while c is not None:
                if isinstance(c, column_list._AccelCell):
                    cells.append(c)
                walk(c)
                c = c.get_next_sibling()
        walk(dialog.shortcuts)
        xid = dialog.get_surface().get_xid()
        subprocess.run(['xdotool', 'windowactivate', '--sync', str(xid)])
        spin(10)
        geo = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', str(xid)], capture_output=True, text=True).stdout
        g = dict(l.split('=') for l in geo.split())
        ox, oy = int(g['X']), int(g['Y'])
        def click(cell):
            ok, pt = cell.compute_point(dialog, Graphene.Point().init(cell.get_width() / 2, cell.get_height() / 2))
            subprocess.run(['xdotool', 'mousemove', str(ox + int(pt.x)), str(oy + int(pt.y)), 'click', '1'], check=True)
            spin(20)
        print("RESULT cells", len(cells), [c.accelerator for c in cells][:8], flush=True)
        print("RESULT rows", [(getattr(c.row, "action", "?"), c.get_mapped()) for c in cells][:6], flush=True)
        cells = [c for c in cells if c.get_mapped() and getattr(c.row, "action", None)]
        a, b = cells[0], cells[1]
        click(a)
        print('RESULT after click a: a.capturing', a.capturing, 'focus', type(dialog.get_focus()).__name__, flush=True)
        click(b)
        print('RESULT after click b: a.capturing', a.capturing, 'b.capturing', b.capturing, flush=True)
        print('RESULT focus is b', dialog.get_focus() is b, dialog.is_active(), flush=True)
        subprocess.run(['xdotool', 'windowfocus', '--sync', str(xid)])
        spin(10)
        print('RESULT b.capturing after windowfocus', b.capturing, dialog.get_focus() is b, flush=True)
        subprocess.run(['xdotool', 'key', 'Escape'], check=True)
        spin(30)
        print('RESULT after Escape: b.capturing', b.capturing, 'dialog visible', dialog.get_visible(), flush=True)
