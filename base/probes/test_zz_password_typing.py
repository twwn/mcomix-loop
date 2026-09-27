import os, shutil, subprocess, time
from gi.repository import Gtk
from . import MComixTest, get_testfile_path, pump, wait_for
from mcomix import constants, icons, main, message_dialog


def prompts():
    return [w for w in Gtk.Window.list_toplevels()
            if isinstance(w, message_dialog.MessageDialog) and w.get_visible()]


class Probe(MComixTest):
    def _run(self, name, library=False):
        for d in (constants.CONFIG_DIR, constants.DATA_DIR, constants.THUMBNAIL_PATH):
            os.makedirs(d, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow()
        main.set_main_window(window)
        window.present()
        for _ in range(20): pump(); time.sleep(0.02)
        if library:
            from mcomix.library import main_dialog
            main_dialog.open_dialog(None, window)
            lib = main_dialog._dialog
            lib.backend.add_book(get_testfile_path('archives', name))
            lib.book_area.display_covers(constants.COLLECTION_ALL)
            for _ in range(50): pump(); time.sleep(0.02)
            print('PROBE library up, prompts=%d' % len(prompts()))
        path = os.path.join(self.tmp_dir, name)
        shutil.copy(get_testfile_path('archives', name), path)
        try:
            window.filehandler.open_file(path)
            ok = wait_for(lambda: bool(prompts()), seconds=10)
            print('PROBE %s prompt shown=%s count=%d' % (name, ok, len(prompts())))
            if not ok:
                return
            dialog = prompts()[0]
            for _ in range(20): pump(); time.sleep(0.02)
            xid = dialog.get_surface().get_xid()
            subprocess.run(['xdotool', 'windowactivate', '--sync', str(xid)])
            subprocess.run(['xdotool', 'windowfocus', '--sync', str(xid)])
            for _ in range(10): pump(); time.sleep(0.02)
            subprocess.run(['xdotool', 'type', '--delay', '30', '--window', str(xid), 'password'], check=True)
            for _ in range(30): pump(); time.sleep(0.02)
            entry = dialog.get_focus()
            text = entry.get_text() if isinstance(entry, Gtk.Editable) else None
            print('PROBE focus=%r text=%r' % (type(entry).__name__, text))
            subprocess.run(['xdotool', 'key', '--window', str(xid), 'Return'], check=True)
            loaded = wait_for(lambda: window.imagehandler.page_is_available(), seconds=10)
            print('PROBE loaded=%s prompts left=%d' % (loaded, len(prompts())))
        finally:
            for p in prompts(): p.destroy()
            if library:
                from mcomix.library import main_dialog
                main_dialog._close_dialog()
                for w in Gtk.Window.list_toplevels():
                    if isinstance(w, main_dialog._LibraryDialog): w.destroy()
            window.terminate_program(); window.destroy(); main.set_main_window(None); pump()

    def test_rar(self): self._run('Encrypted.rar')
    def test_zip(self): self._run('Encrypted.zip')
    def test_rar_library(self): self._run('Encrypted.rar', library=True)
