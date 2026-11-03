import os, subprocess
from gi.repository import Gtk
from test import MComixTest, wait_for
from mcomix import constants, status, theme
from mcomix.preferences import prefs

OUT = os.environ['SHOT_OUT']

class Shot(MComixTest):
    def test_shot(self):
        theme.follow_theme()
        prefs['statusbar fields'] = 127
        bar = status.Statusbar()
        window = Gtk.Window()
        window.set_default_size(1100, -1)
        window.set_decorated(False)
        column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        column.append(bar)
        filler = Gtk.Label(label='page area'); filler.set_vexpand(True); column.append(filler)
        window.set_child(column)
        window.present()
        bar.set_root('Pepper & Carrot.cbz')
        for page, name, size, res in ((9, 'page-009.jpg', '870.4 KiB', ((1200, 1800, 0.453, False),)),
                                       (10, 'page-010-long-name.jpg', '1.2 MiB', ((800, 1111, 1.0, False),)),
                                       (11, 'p11.jpg', '99 B', ((1200, 1800, 0.453, False),))):
            bar.set_page_number([page], 120)
            bar.set_file_number(3, 12)
            bar.set_filename(name)
            bar.set_filesize(size)
            bar.set_resolution(res)
            bar.set_date('2024-05-06, 07:08:09')
            bar.update()
            wait_for(lambda: False, seconds=1)
            path = '%s-%d.png' % (OUT, page)
            V = Gtk.Orientation.VERTICAL
            print('BAR', bar.measure(V, -1)[:2], bar.measure(V, 1100)[:2], window.get_height(), bar.get_size_request())
            for f in list(getattr(bar, '_separators', {}).values())[:1]: print('SEP', f.measure(V, -1)[:2])
            for f in getattr(bar, '_fields', {}).values():
                print('FV', f.measure(V, -1)[:2], f.measure(V, 50)[:2])
                print('F', repr(f.get_text()), f.get_visible(), f.get_mapped(), f.get_width(), f.get_height(), f.get_layout().get_pixel_size(), f.get_opacity())
            subprocess.run(['import', '-window', 'root', '-crop', '1100x26+0+0', path], check=True)
        window.destroy()
