import subprocess, time
from gi.repository import Graphene, Gtk
from . import MComixTest, pump
from mcomix import thumbnail_list

def settle(n=25):
    for _ in range(n): pump(); time.sleep(0.02)

def screen_point(widget, window):
    ok, pt = widget.compute_point(window, Graphene.Point().init(widget.get_width() / 2, widget.get_height() / 2))
    dx, dy = window.get_surface_transform()
    return int(pt.x + dx), int(pt.y + dy)

class Probe(MComixTest):
    def test_blink(self):
        view = thumbnail_list.ThumbnailGridView()
        view.generate_thumbnail = lambda uid: None
        view.set_thumbnail_size(48); view.set_reorderable(True)
        scroller = Gtk.ScrolledWindow(); scroller.set_child(view)
        window = Gtk.Window(); window.set_default_size(300, 300); window.set_child(scroller)
        window.present(); pump()
        view.set_items(thumbnail_list.ThumbnailItem(i) for i in range(200)); settle()
        self.addCleanup(window.destroy); self.addCleanup(view.release)
        adj = scroller.get_vadjustment(); adj.set_value(adj.get_upper() / 2); settle()
        cells = [c for c in view._each_cell() if c.get_mapped() and 40 < c.compute_bounds(window)[1].get_y() < 220]
        cell = min(cells, key=lambda c: c.position); pa = cell.position
        x, y = screen_point(cell, window)
        subprocess.run(['xdotool', 'mousemove', '--window', str(window.get_surface().get_xid()), str(x), str(y)], check=True); settle(5)
        seen = []
        handler = adj.connect('value-changed', lambda a: seen.append(round(a.get_value())))
        before = adj.get_value()
        target = [c for c in view._each_cell() if c.position == pa + 4][0]
        tx, ty = screen_point(target, window)
        xid = str(window.get_surface().get_xid())
        subprocess.run(['xdotool', 'mousedown', '1'], check=True); settle(5)
        for i in range(1, 11):
            subprocess.run(['xdotool', 'mousemove', '--window', xid, str(x + (tx - x) * i // 10), str(y + (ty - y) * i // 10)], check=True); settle(2)
        settle(5); subprocess.run(['xdotool', 'mouseup', '1'], check=True); settle()
        print('PROBE item at dest', view.get_item(pa + 4).uid)
        adj.disconnect(handler)
        f = window.get_focus()
        fpos = f.get_first_child().position if f is not None and f.get_first_child() is not None and hasattr(f.get_first_child(), 'position') else None
        print('PROBE before %.0f after %.0f values seen %s focus on %s (moved %s)' % (before, adj.get_value(), seen, view.get_item(fpos).uid if fpos is not None else type(f).__name__, pa))
