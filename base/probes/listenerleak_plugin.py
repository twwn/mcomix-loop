"""Names every test after which the bookmarks store still has listeners
whose objects are alive once the collector has run."""
import gc
import os


def pytest_runtest_logfinish(nodeid, location):
    from mcomix import bookmark_backend, callback
    store = bookmark_backend.BookmarksStore
    gc.collect()
    alive = []
    for name, value in vars(store).items():
        if isinstance(value, callback.CallbackList):
            for ref, func in value._CallbackList__callbacks:
                obj = ref() if ref is not None else func
                if obj is not None:
                    alive.append('%s:%s' % (name, type(obj).__name__))
    if alive:
        with open(os.environ['LISTENERLEAK'], 'a') as out:
            out.write('%s\t%s\t%d\t%s\n' % (os.environ.get('PYTEST_XDIST_WORKER', '-'), nodeid, len(alive), ' '.join(sorted(set(alive)))))
