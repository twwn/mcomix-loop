"""Deliver the book's pages late, as the loaded Windows runner did.

Extraction waits until the test first changes the fullscreen state (or
half a second has passed), and leaving fullscreen holds the main thread
until a page has been posted, so its arrival lands in the test's pump.
"""
import threading

from mcomix import archive_extractor, event, main

_gate = threading.Event()
_posted = threading.Event()

_extract = archive_extractor.Extractor._extract_file


def _late_extract(self, name):
    _gate.wait(0.5)
    _extract(self, name)
    _posted.set()


_state = event.EventHandler.window_state_event


def _opening_state(self, *args):
    _gate.set()
    return _state(self, *args)


_soon = main.MainWindow.restore_window_geometry_soon


def _held_soon(self):
    _posted.wait(5)
    return _soon(self)


archive_extractor.Extractor._extract_file = _late_extract
event.EventHandler.window_state_event = _opening_state
main.MainWindow.restore_window_geometry_soon = _held_soon


def pytest_runtest_setup(item):
    _gate.clear()
    _posted.clear()
