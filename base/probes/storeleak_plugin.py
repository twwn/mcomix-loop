"""Names every test that leaves the process's bookmarks store holding
bookmarks or a window when it is over."""
import os
import pytest




def pytest_runtest_logfinish(nodeid, location):
    from mcomix import bookmark_backend
    store = bookmark_backend.BookmarksStore
    left = []
    if store._bookmarks:
        left.append('%d bookmarks' % len(store._bookmarks))
    if store._window is not None:
        left.append('window %s' % type(store._window).__name__)
    if left:
        with open(os.environ['STORELEAK'], 'a') as out:
            out.write('%s\t%s\n' % (nodeid, ', '.join(left)))
