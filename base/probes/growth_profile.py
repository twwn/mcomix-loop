"""pytest plugin: profile the first and the last quarter of the tests run.

Writes STATE/scratch/prof_first.out and prof_last.out (pstats), each the
tests of that quarter from setup to teardown, for comparing what got
slower in a process that has run many tests.  QUARTER sets the count.
"""
import cProfile
import os

_n = [0]
_total = int(os.environ.get('QUARTER', '55'))
_prof = {'first': cProfile.Profile(), 'last': cProfile.Profile()}
_out = os.path.expanduser('~/.claude/skills/mcomix-loop/state/scratch/prof_%s.out')


def _which():
    if _n[0] < _total:
        return 'first'
    if _n[0] >= 3 * _total:
        return 'last'
    return None


def pytest_runtest_setup(item):
    which = _which()
    if which:
        _prof[which].enable()


def pytest_runtest_teardown(item, nextitem):
    pass


def pytest_runtest_logreport(report):
    if report.when != 'teardown':
        return
    which = _which()
    if which:
        _prof[which].disable()
    _n[0] += 1


def pytest_sessionfinish(session):
    for which, prof in _prof.items():
        prof.dump_stats(_out % which)
