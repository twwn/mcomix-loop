import os, shutil, unittest.mock
from . import get_testfile_path, wait_for, pump
from . import test_main_window as tmw
from mcomix.preferences import prefs


class Listed(tmw.MainWindowTest):
    def _lib(self):
        books = []
        for rel in ('x/C.cbz', 'y/B.cbz', 'x/A.cbz', 'z/D.cbz'):
            p = os.path.join(self.tmp_dir, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copy(get_testfile_path('archives', '01-ZIP-Normal.zip'), p)
            books.append(p)
        return books

    def _open(self, path, **kw):
        fh = self.window.filehandler
        fh.open_file(path, **kw)
        assert wait_for(lambda: fh.file_loaded and self.window.imagehandler.get_number_of_pages() > 2, 20)
        pump(200)

    def _where(self):
        fh = self.window.filehandler
        p = fh.get_path_to_base() or '-'
        return os.path.relpath(p, self.tmp_dir), fh.get_file_number()

    def _step(self):
        self.window.filehandler.next_archive()
        wait_for(lambda: self.window.filehandler.file_loaded, 10); pump(200)
        return self._where()

    def test_rename(self):
        books = self._lib()
        self._open(books[1], listed=books)
        print('\nrename: opened', self._where())
        target = os.path.join(os.path.dirname(books[1]), 'B2.cbz')
        self.window.filehandler.release_archive()
        os.rename(books[1], target)
        self.window.file_actions._book_moved(books[1], target)
        wait_for(lambda: self.window.filehandler.file_loaded, 10); pump(200)
        print('  after rename', self._where())
        print('  next ->', self._step())

    def test_delete(self):
        books = self._lib()
        self._open(books[2], listed=books)
        print('\ndelete: opened', self._where())
        self.window.filehandler.release_archive()
        os.remove(books[2])
        self.window.file_actions._leave_deleted(books[2])
        wait_for(lambda: self.window.filehandler.file_loaded, 10); pump(200)
        print('  after delete', self._where())
