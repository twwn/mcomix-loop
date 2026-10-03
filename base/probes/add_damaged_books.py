"""What LibraryBackend.add_book() does with truncated and damaged archives.

Run from the checkout on MComixTest: each book is cut at 10, 50 and 90 % (a
zip also gets 200 zero bytes in its middle) and added; prints the answer
or the exception per book.
"""
import os, sys
sys.path.insert(0, os.environ.get('TREE') or os.getcwd())   # the checkout this runs from, or TREE
from test import MComixTest, get_testfile_path
from test.test_mobi import _book, _image
from mcomix import constants
from mcomix.library import backend


class Probe(MComixTest):
    def test_probe(self):
        os.makedirs(constants.DATA_DIR, exist_ok=True)
        lib = backend.LibraryBackend()
        self.addCleanup(lib.close)
        cases = {'b.mobi': _book([_image('JPEG')])[:150]}
        for src in ('02-TAR-Normal.tar', '03-RAR-Normal.rar', '04-7Z-Normal.7z', '01-ZIP-Normal.zip'):
            with open(get_testfile_path('archives', src), 'rb') as f:
                data = f.read()
            for frac in (0.1, 0.5, 0.9):
                cases['%s-%s' % (frac, src)] = data[:int(len(data) * frac)]
            if src.endswith('.zip'):
                cases['mid-' + src] = data[:30] + b'\0' * 200 + data[230:]
        for name, data in cases.items():
            path = os.path.join(self.tmp_dir, name)
            with open(path, 'wb') as f:
                f.write(data)
            try:
                r = lib.add_book(path)
            except Exception as e:
                r = 'RAISED %s: %s' % (type(e).__name__, str(e)[:60])
            print('\nPROBE', name, r)
