"""Out of the suite: real Ctrl and Ctrl+Shift clicks on the sidebar."""
import os
import subprocess
import time

from gi.repository import Graphene, GLib

from . import MComixTest, get_testfile_path, pump, wait_for

from mcomix import constants, icons, main
from mcomix.preferences import prefs


def x(*args):
    subprocess.run(['xdotool', *map(str, args)], check=True)


class T(MComixTest):
    def test_it(self):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        prefs['show thumbnails'] = True
        icons.load_icons()
        w = main.MainWindow(open_path=get_testfile_path('archives', '01-ZIP-Normal.zip'))
        main.set_main_window(w)
        self.addCleanup(lambda: (w.terminate_program(), w.destroy(), main.set_main_window(None), pump(500)))
        w.present()
        self.assertTrue(wait_for(lambda: w.imagehandler.get_number_of_pages() > 0, seconds=20))
        bar = w.thumbnailsidebar
        self.assertTrue(wait_for(lambda: bar._loaded and bar._list.get_width() > 0, seconds=20))
        pump(800)
        lst = bar._list
        xid = w.get_surface().get_xid()
        x('windowfocus', '--sync', xid)
        pump(300)
        w.was_out_of_focus = False
        sx, sy = w.get_surface_transform()

        def point(row):
            # Rows are of one height: find row centre by probing.
            h = lst.get_height()
            for yy in range(0, h, 4):
                if lst.position_at(lst.get_width() / 2, yy) == row:
                    ok, p = lst.compute_point(w, Graphene.Point().init(lst.get_width() / 2, yy + 20))
                    return int(p.x + sx), int(p.y + sy)
            raise AssertionError('no row %d' % row)

        def step():
            pump(100)
            time.sleep(0.05)
            pump(100)

        def click(row, *keys):
            px, py = point(row)
            x('mousemove', '--window', xid, px, py)
            step()
            for k in keys:
                x('keydown', k)
            step()
            x('click', 1)
            step()
            for k in reversed(keys):
                x('keyup', k)
            step()

        from gi.repository import Gtk
        def texts():
            out=[]
            for t in Gtk.Window.list_toplevels():
                if t is not w and t.get_visible():
                    out.append((type(t).__name__, getattr(getattr(t,'_primary',None),'get_text',lambda:'')()))
            return out
        for c in lst.observe_controllers():
            if isinstance(c, Gtk.GestureClick) and c.get_button()==0:
                for sig in ('pressed','released','stopped','unpaired-release'):
                    c.connect(sig, lambda g,*a,sig=sig: print('SIG',sig,a[:3]))
                c.connect('cancel', lambda g,*a: print('SIG cancel'))
        print('page', w.imagehandler.get_current_page())
        click(1, 'ctrl')
        print('ctrl+click row1: selected', w.selected_pages, 'page', w.imagehandler.get_current_page())
        click(1, 'ctrl')
        print('again: selected', w.selected_pages)
        click(1, 'ctrl', 'shift')
        print('ctrl+shift row1: swap_page', w.swap_page, 'page', w.imagehandler.get_current_page())
        before = w.imagehandler.get_image_files()
        click(2, 'ctrl', 'shift')
        after = w.imagehandler.get_image_files()
        print('ctrl+shift row2: swap_page', w.swap_page, 'swapped', before[1:3] == after[2:0:-1])
        for t in Gtk.Window.list_toplevels():
            if t is not w and t.get_visible():
                t.destroy()
        pump(300)
        x('windowfocus', '--sync', xid)
        pump(300)
        w.was_out_of_focus = False
        before = w.imagehandler.get_image_files()
        px, py = point(0)
        qx, qy = point(1)
        x('mousemove', '--window', xid, px, py)
        step()
        x('keydown', 'ctrl')
        x('keydown', 'shift')
        step()
        x('mousedown', 1)
        step()
        for n in range(1, 6):
            x('mousemove', '--window', xid, px + (qx - px) * n // 5, py + (qy - py) * n // 5)
            step()
        x('mouseup', 1)
        step()
        x('keyup', 'shift')
        x('keyup', 'ctrl')
        step()
        after = w.imagehandler.get_image_files()
        print('dialogs', texts())
        for t in Gtk.Window.list_toplevels():
            if t is not w and t.get_visible():
                t.destroy()
        pump(300)
        x('windowfocus', '--sync', xid)
        pump(300)
        w.was_out_of_focus = False
        print('drag row0->row1: swapped', before[:2] == after[1::-1], 'swap_page', w.swap_page)
        click(3)
        print('dialogs', texts())
        for t in Gtk.Window.list_toplevels():
            if t is not w and t.get_visible():
                t.destroy()
        pump(300)
        print('plain click row3: page', w.imagehandler.get_current_page(), 'selected', w.selected_pages)
