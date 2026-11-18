"""A real right click on a file row and a folder row of the file chooser:
which items its menu shows, and which of them are greyed out."""
import os, shutil, subprocess, sys, time, unittest
from gi.repository import Gtk, Graphene
from test import MComixTest, get_testfile_path, pump
from mcomix import constants, icons, main, file_chooser_simple_dialog as fcs

MODE = {'open': Gtk.FileChooserAction.OPEN, 'save': Gtk.FileChooserAction.SAVE}[os.environ.get('MODE', 'open')]


def sh(*a):
    subprocess.run(['xdotool', *a], check=False)


def spin(n=15):
    for _ in range(n):
        pump(); time.sleep(0.02)


def walk(w, out=None, popovers=True):
    out = [] if out is None else out
    c = w.get_first_child()
    while c is not None:
        out.append(c)
        if popovers or not isinstance(c, Gtk.Popover):
            walk(c, out, popovers)
        c = c.get_next_sibling()
    return out


class Probe(MComixTest):
    def test_menu(self):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow(); main.set_main_window(window); pump()
        os.mkdir(os.path.join(self.tmp_dir, 'afolder'))
        shutil.copy(get_testfile_path('archives', '01-ZIP-Normal.zip'),
                    os.path.join(self.tmp_dir, 'book.zip'))

        def run(name):
            dlg = fcs.SimpleFileChooserDialog(MODE, window, folder=self.tmp_dir)
            if MODE == Gtk.FileChooserAction.SAVE:
                dlg.set_save_name('page.png')
            dlg.files_chosen = lambda *a: None
            dlg.set_visible(True); spin(40)
            xid = dlg.get_surface().get_xid()
            sh('windowfocus', '--sync', str(xid)); spin()
            row = None
            for w in walk(dlg._listing, popovers=False):
                if w.get_css_name() == 'row':
                    texts = [c.get_text() for c in walk(w) if isinstance(c, Gtk.Inscription)]
                    texts += [c.get_label() for c in walk(w) if isinstance(c, Gtk.Label)]
                    if name in texts:
                        row = w
            if row is None:
                print('PROBE', name, 'row not found'); dlg.destroy(); spin(); return
            ok, pt = row.compute_point(dlg, Graphene.Point().init(row.get_width() / 2, row.get_height() / 2))
            ox, oy = dlg.get_surface_transform()
            sh('mousemove', '--window', str(xid), str(int(pt.x + ox)), str(int(pt.y + oy))); spin(5)
            sh('click', '3'); spin(30)
            menus = [p for p in walk(dlg.filechooser) if isinstance(p, Gtk.PopoverMenu) and p.get_visible()]
            print('PROBE selected', [f.get_path() for f in (dlg.filechooser.get_files() or [])])
            if os.environ.get('ENABLE'):
                for a in ('item.rename', 'item.delete', 'item.trash', 'item.open-folder'):
                    dlg.filechooser.action_set_enabled(a, True)
                spin(5)
            print('PROBE', os.environ.get('MODE', 'open'), name, 'menus shown', len(menus))
            for menu in menus:
                for item in walk(menu):
                    if item.get_css_name() == 'modelbutton':
                        labels = [c.get_label() for c in walk(item) if isinstance(c, Gtk.Label)]
                        print('PROBE   ', labels, 'visible' if item.get_visible() else 'HIDDEN',
                              'sensitive' if item.is_sensitive() else 'GREYED')
                if os.environ.get('ACT'):
                    menu.popdown(); spin()
                    dlg.filechooser.activate_action(os.environ['ACT'], None); spin(30)
                    print('PROBE after', os.environ['ACT'], sorted(os.listdir(self.tmp_dir)))
                    for w in walk(dlg.filechooser):
                        if isinstance(w, (Gtk.Popover,)) and w.get_visible():
                            print('PROBE   popover', type(w).__name__, [c.get_text() for c in walk(w) if isinstance(c, Gtk.Entry)], [c.get_label() for c in walk(w) if isinstance(c, (Gtk.Label, Gtk.Button)) and c.get_label()])
                    for t in Gtk.Window.list_toplevels():
                        if t.get_visible() and t is not dlg and t is not window:
                            print('PROBE   window', type(t).__name__, [c.get_label() for c in walk(t) if isinstance(c, Gtk.Label) and c.get_label()][:6])
                            t.destroy()
                menu.popdown()
            spin()
            dlg.destroy(); spin()

        run('book.zip')
        if not os.environ.get('ACT'):
            run('afolder')
        window.terminate_program(); window.destroy(); main.set_main_window(None); pump()


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], 'Probe'], exit=False)
    sys.stdout.flush(); os._exit(0)
