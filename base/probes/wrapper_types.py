"""pytest plugin: at session end, the GObject wrapper types and Python
types most numerous among what is still alive."""
import collections
import gc


def pytest_sessionfinish(session):
    gc.collect()
    from gi.repository import GObject
    objs = gc.get_objects()
    wrappers = collections.Counter(type(o).__qualname__ for o in objs
                                   if isinstance(o, GObject.Object))
    plain = collections.Counter(type(o).__qualname__ for o in objs)
    print('\nWRAPPERS', wrappers.most_common(15))
    print('TYPES', plain.most_common(15))
