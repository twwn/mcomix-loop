"""A pytest plugin for wine_pytest.sh, loaded with -p before any conftest.

Under Wine (11.22 staging), a start often deadlocked while libgtk-4-1.dll
loaded: the main thread stopped in wined3d.dll's process attach, holding
the loader lock, while GIO's Windows app-info thread, enumerating packages
through RoActivateInstance(Windows.Management.Deployment.PackageManager),
waited for that lock. 6 starts in 20, and 12 in 30, hung so on 2026-11-18.
Asking GIO for every app first waits for that thread's work before GTK
loads: 0 hangs in 50 starts the same day.

The plugin also says on stderr when collection is done, which is past the
import of GTK, so that wine_pytest.sh can tell a start that hung anyway.
"""
import sys

import gi
from gi.repository import Gio

Gio.AppInfo.get_all()
del gi


def pytest_collection_finish(session):
    sys.stderr.write('wine_pytest: collected\n')
    sys.stderr.flush()
