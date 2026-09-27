"""Where does the library chooser test segfault?  VARIANT picks:
none - no chooser; main - chooser over the main window; lib - over a
Gtk.Window subclass; plain - over a plain Gtk.Window."""
import os, sys, unittest
sys.path.insert(0, '/tmp/mcomix-git')
from gi.repository import Gtk
from test import MComixTest, pump
from mcomix import constants, icons, main

VARIANT = os.environ.get('VARIANT', 'none')

class _Library(Gtk.Window):
    def add_books(self, paths, collection):
        pass

class Probe(MComixTest):
    def test_probe(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow()
        main.set_main_window(window)
        parent = {'none': None, 'main': window, 'lib': _Library(), 'plain': Gtk.Window()}[VARIANT]
        pump()
        from mcomix import file_chooser_library_dialog as m
        if os.environ.get('NOREMOVE'):
            from mcomix import file_chooser_base_dialog as b
            orig = m._LibraryFileChooserDialog.__init__
            real_remove = Gtk.FileChooserWidget.remove_filter
            Gtk.FileChooserWidget.remove_filter = lambda self, f: print('remove skipped', flush=True)
        if parent is not None:
            m.open_library_filechooser_dialog(parent)
            pump()
            print('opened', m._library_filechooser_dialog, flush=True)
            m.close_library_filechooser_dialog()
            pump()
            print('closed', flush=True)
            if parent is not window:
                parent.destroy()
                pump()
        import gc
        print('collecting', flush=True)
        gc.collect()
        print('collected', flush=True)
        window.terminate_program()
        print('terminated', flush=True)
        window.destroy()
        main.set_main_window(None)
        pump()

unittest.main(argv=[sys.argv[0], 'Probe'], exit=False)
sys.stdout.flush(); os._exit(0)
