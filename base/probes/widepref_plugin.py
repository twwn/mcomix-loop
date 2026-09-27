"""pytest -p widepref_plugin: every test's default window is WIDEPREF
pixels wide (run under a screen large enough to allow it), as a window
may open wider elsewhere than it does under a 640 by 480 Xvfb."""
import os


def pytest_configure(config):
    import test
    test.default_prefs['window width'] = int(os.environ.get('WIDEPREF', '1000'))
