import subprocess, time
from gi.repository import Graphene
from .test_openwith_editor import OpenWithEditorTest as _Base
from . import pump
from mcomix import column_list
from mcomix.dialog import Response
from mcomix.preferences import prefs


def spin(n):
    for _ in range(n):
        pump(); time.sleep(0.02)


class Probe(_Base):
    def _cell(self):
        found = []
        def walk(w):
            c = w.get_first_child()
            while c is not None:
                if isinstance(c, column_list._EditableCell) and c.get_text() == 'gedit %F':
                    found.append(c)
                walk(c)
                c = c.get_next_sibling()
        walk(self.editor)
        return found[0]

    def _real(self, target):
        self.editor.present()
        spin(20)
        xid = self.editor.get_surface().get_xid()
        subprocess.run(['xdotool', 'windowactivate', '--sync', str(xid)])
        subprocess.run(['xdotool', 'windowfocus', '--sync', str(xid)])
        spin(10)
        g = dict(l.split('=') for l in subprocess.run(['xdotool', 'getwindowgeometry', '--shell', str(xid)], capture_output=True, text=True).stdout.split())
        ox, oy = int(g['X']), int(g['Y'])
        def click(w, n=1):
            ok, pt = w.compute_point(self.editor, Graphene.Point().init(w.get_width() / 2, w.get_height() / 2))
            subprocess.run(['xdotool', 'mousemove', str(ox + int(pt.x)), str(oy + int(pt.y)), 'click', '--repeat', str(n), '--delay', '80', '1'], check=True)
            spin(20)
        cell = self._cell()
        click(cell, 2)
        print('RESULT after double click editing', cell.get_editing(), type(self.editor.get_focus()).__name__, flush=True)
        if not cell.get_editing():
            cell.grab_focus(); cell.start_editing(); spin(10)
        subprocess.run(['xdotool', 'key', 'ctrl+a'], check=True)
        subprocess.run(['xdotool', 'type', '--delay', '30', 'kate %F'], check=True)
        spin(20)
        print('RESULT typed', repr(cell.get_text()), 'editing', cell.get_editing(), flush=True)
        if target == 'save':
            click(self.editor._save_button)
            spin(20)
            print('RESULT after Save click: stored', prefs['openwith commands'][0][1], 'visible', self.editor.get_visible(), flush=True)
        else:
            subprocess.run(['xdotool', 'key', 'Return'], check=True)
            spin(20)
            print('RESULT after Return: editing', cell.get_editing(), 'changed', self.editor._changed, flush=True)

    def test_save(self): self._real('save')
    def test_enter(self): self._real('enter')
