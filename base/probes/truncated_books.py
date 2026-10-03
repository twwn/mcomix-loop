"""Every truncation of a two-image MOBI book: where MobiArchive fails, and how.

Run from the checkout on MComixTest; prints a count per (stage, exception).
"""
import collections, os, sys
sys.path.insert(0, os.environ.get('TREE') or os.getcwd())   # the checkout this runs from, or TREE
from test import MComixTest
from test.test_mobi import _book, _image
from mcomix.archive import mobi


class Probe(MComixTest):
    def test_probe(self):
        data = _book([_image('JPEG'), _image('PNG')])
        path = os.path.join(self.tmp_dir, 'b.mobi')
        seen = collections.Counter()
        for n in range(60, len(data)):
            with open(path, 'wb') as f:
                f.write(data[:n])
            stage = 'open'
            try:
                a = mobi.MobiArchive(path)
                stage = 'list'
                names = list(a.iter_contents())
                stage = 'extract'
                for name in names:
                    a.extract(name, self.tmp_dir)
                a.close()
                seen['ok'] += 1
            except Exception as e:
                seen[(stage, type(e).__name__)] += 1
        print('\nPROBE', len(data), dict(seen))
