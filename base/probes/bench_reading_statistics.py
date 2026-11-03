import os, sys, time, unittest
sys.path.insert(0, os.getcwd())
from test import MComixTest
from mcomix import constants

class Probe(MComixTest):
    def test_bench(self):
        os.makedirs(constants.DATA_DIR, exist_ok=True)
        from mcomix.library import backend
        lib = backend.LibraryBackend() if hasattr(backend, 'LibraryBackend') else backend._LibraryBackend()
        N = 20000
        with lib.transaction():
            for i in range(N):
                lib.execute('insert into book (id, name, path, pages, format, size) values (?, ?, ?, ?, ?, ?)', (i + 1, 'b%d' % i, '/x/b%d.zip' % i, 20, 0, 1))
                lib.execute('insert into recent (book, page, time_set) values (?, ?, ?)', (i + 1, 1 + i % 20, '2026-10-%02d 12:%02d:%02d.%06d' % (1 + i % 28, i % 60, i % 60, i)))
        ids = list(range(1, N + 1))
        times = []
        for _ in range(5):
            t = time.perf_counter(); s = lib.reading_statistics(ids); times.append(time.perf_counter() - t)
        print('stats', s, 'median %.1f ms' % (sorted(times)[2] * 1e3), flush=True)
        lib.close()

if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], 'Probe'], exit=False); sys.stdout.flush(); os._exit(0)
