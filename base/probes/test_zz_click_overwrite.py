import os, subprocess, time, unittest.mock
from gi.repository import Gio, Gtk, Graphene
from . import pump, wait_for
from .test_edit_dialog import EditArchiveDialogTest as _Base
from mcomix import constants, message_dialog, widgets
from mcomix.dialog import Response

def click(widget, window):
    ok, pt = widget.compute_point(window, Graphene.Point().init(widget.get_width() / 2, widget.get_height() / 2))
    dx, dy = window.get_surface_transform()
    xid = window.get_surface().get_xid()
    x, y = int(pt.x + dx), int(pt.y + dy)
    subprocess.run(['xdotool', 'mousemove', '--window', str(xid), str(x), str(y)], check=True)
    for _ in range(10): pump(); time.sleep(0.02)
    subprocess.run(['xdotool', 'click', '1'], check=True)
    for _ in range(20): pump(); time.sleep(0.02)

class Probe(_Base):
    def _run(self, fix):
        target = os.path.join(self.tmp_dir, 'taken.cbz')
        open(target, 'wb').write(b'old')
        packed = []
        real = message_dialog.MessageDialog
        probe = self
        class made(real):
            def __init__(self, parent, *a, **k):
                if fix:
                    k['modal'] = True
                    parent = probe._chooser()
                super().__init__(parent, *a, **k)
        self.dialog.present()
        for _ in range(10): pump(); time.sleep(0.02)
        with unittest.mock.patch.object(self.dialog, '_pack_archive', packed.append), \
             unittest.mock.patch.object(message_dialog, 'MessageDialog', made):
            self.dialog._response(self.dialog, constants.RESPONSE_SAVE_AS)
            pump()
            chooser = self._chooser()
            chooser.filechooser.set_file(Gio.File.new_for_path(target))
            wait_for(lambda: widgets.chooser_paths(chooser.filechooser) == [target], seconds=5)
            chooser.response(Response.OK)
            for _ in range(20): pump(); time.sleep(0.02)
            dialog = [w for w in Gtk.Window.list_toplevels() if isinstance(w, message_dialog.MessageDialog) and w.get_visible()][0]
            click(dialog.get_widget_for_response(Response.OK), dialog)
            print('PROBE fix=%s packed=%s dialog still up=%s' % (fix, len(packed), dialog.get_visible()))
            dialog.destroy()
    def test_as_is(self): self._run(False)
    def test_fixed(self): self._run(True)
