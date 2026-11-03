"""Real double clicks on each part of the file chooser: which reach files_chosen."""
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
def walk(w, out=None):
    out = [] if out is None else out
    c = w.get_first_child()
    while c is not None:
        out.append(c); walk(c, out); c = c.get_next_sibling()
    return out

class Probe(MComixTest):
    def test_dbl(self):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow(); main.set_main_window(window); pump()
        os.mkdir(os.path.join(self.tmp_dir, 'afolder'))
        shutil.copy(get_testfile_path('images', 'blue.png') if False else get_testfile_path('archives', '01-ZIP-Normal.zip'), os.path.join(self.tmp_dir, 'book.zip'))
        def run(what, find):
            dlg = fcs.SimpleFileChooserDialog(MODE, window, folder=self.tmp_dir)
            if MODE == Gtk.FileChooserAction.SAVE:
                dlg.set_save_name('page.png')
            chosen = []
            dlg.files_chosen = lambda files, *a: chosen.append(list(files))
            dlg.set_visible(True); spin(40)
            xid = dlg.get_surface().get_xid()
            sh('windowfocus', '--sync', str(xid)); spin()
            w = find(dlg)
            if w is None:
                print('PROBE', what, 'not found'); dlg.destroy(); spin(); return
            ok, pt = w.compute_point(dlg, Graphene.Point().init(w.get_width() / 2, min(w.get_height() / 2, w.get_height() - 4)))
            ox, oy = dlg.get_surface_transform()
            sh('mousemove', '--window', str(xid), str(int(pt.x + ox)), str(int(pt.y + oy))); spin(5)
            sh('click', '--repeat', '2', '--delay', '60', '1'); spin(25)
            print('PROBE', os.environ.get('MODE', 'open'), what, [type(w).__name__, w.get_css_name()], 'chosen', [[os.path.relpath(p, self.tmp_dir) for p in c] for c in chosen], 'folder', os.path.basename((dlg.filechooser.get_current_folder().get_path() if dlg.filechooser.get_current_folder() else '') or ''), flush=True)
            dlg.destroy(); spin()
        def row(name):
            def find(dlg):
                lst = dlg._listing
                if not getattr(self, 'dumped', False):
                    self.dumped = True
                    print('PROBE listing', lst)
                    def dump(w, d=0):
                        if d < 7:
                            print('PROBE ', ' ' * d, type(w).__name__, w.get_css_name(), w.get_text() if isinstance(w, Gtk.Inscription) else '')
                            c = w.get_first_child()
                            while c is not None:
                                dump(c, d + 1); c = c.get_next_sibling()
                    dump(lst)
                for w in walk(lst):
                    if type(w).__name__ == 'GtkColumnViewRowWidget' or w.get_css_name() == 'row':
                        texts = [c.get_text() for c in walk(w) if isinstance(c, Gtk.Inscription)] + [c.get_label() for c in walk(w) if isinstance(c, Gtk.Label)]
                        if name in texts:
                            return w
            return find
        run('file row', row('book.zip'))
        run('folder row', row('afolder'))
        run('column header', lambda d: next((b for b in walk(d._listing) if type(b).__name__ == 'GtkColumnViewTitle'), None))
        run('place row', lambda d: next((b for b in walk(d.filechooser) if isinstance(b, Gtk.ListBoxRow) and b.get_mapped() and b.get_height() > 10), None))
        def empty(dlg):
            lv = next((w for w in walk(dlg.filechooser) if isinstance(w, Gtk.ListView)), None)
            return lv
        run('list itself (lower half: empty)', empty)
        window.terminate_program(); window.destroy(); main.set_main_window(None); pump()

if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], 'Probe'], exit=False)
    sys.stdout.flush(); os._exit(0)
