"""Probe: what Shelf.show_books() pays to learn whether the library
holds any book, at 20,000 books: get_books_in_collection(None) against
one EXISTS statement, and the display that follows."""
import time

from test import MComixTest

from mcomix import constants
from mcomix.library import backend

BOOKS = 20000


class HasBooksProbe(MComixTest):

    def test_probe(self):
        import os
        os.makedirs(constants.DATA_DIR, exist_ok=True)
        library = backend.LibraryBackend()
        with library.transaction():
            library._con.executemany(
                'insert into book (name, path, pages, format, size, added)'
                ' values (?, ?, 1, 1, 1, "2020-01-01")',
                [('b%05d.zip' % i, '/x/b%05d.zip' % i) for i in range(BOOKS)])

        def best(call, runs=15):
            times = []
            for _ in range(runs):
                start = time.perf_counter()
                call()
                times.append(time.perf_counter() - start)
            return min(times) * 1000, sorted(times)[runs // 2] * 1000

        print('PROBE ids    best %.2f median %.2f ms' % best(
            lambda: bool(library.get_books_in_collection(None))))
        print('PROBE exists best %.2f median %.2f ms' % best(
            lambda: library.fetchone('select exists (select 1 from book)')))
        all_books = library.get_collection_by_id(constants.COLLECTION_ALL)
        print('PROBE get_books (display) best %.2f median %.2f ms' % best(
            lambda: all_books.get_books(), runs=5))
        library.close()
