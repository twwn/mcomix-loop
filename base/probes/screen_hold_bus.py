"""ScreenHold against a real bus: run under `dbus-run-session`, never on
the user's own session bus.  Owns org.freedesktop.portal.Desktop on the
private bus with an Inhibit interface, holds and releases through
mcomix.screen_saver's real _session_bus, and prints what the stand-in
portal received."""
import os
import sys

from gi.repository import Gio, GLib

from mcomix import screen_saver

assert os.environ.get('PROBE_PRIVATE_BUS') == '1', 'run under dbus-run-session'

XML = '''<node>
 <interface name="org.freedesktop.portal.Inhibit">
  <method name="Inhibit"><arg type="s" direction="in"/><arg type="u" direction="in"/>
   <arg type="a{sv}" direction="in"/><arg type="o" direction="out"/></method>
 </interface>
 <interface name="org.freedesktop.portal.Request"><method name="Close"/></interface>
</node>'''
info = Gio.DBusNodeInfo.new_for_xml(XML)
loop = GLib.MainLoop()
seen = []
REQUEST = '/org/freedesktop/portal/desktop/request/1_1/probe'


def called(connection, sender, path, interface, method, parameters, invocation):
    seen.append((path, interface, method, parameters.unpack()))
    print('portal got', path, interface, method, parameters.unpack(), flush=True)
    if method == 'Inhibit':
        invocation.return_value(GLib.Variant('(o)', (REQUEST,)))
    else:
        invocation.return_value(None)
        GLib.idle_add(loop.quit)


def acquired(connection, name):
    connection.register_object('/org/freedesktop/portal/desktop',
                               info.interfaces[0], called, None, None)
    connection.register_object(REQUEST, info.interfaces[1], called, None, None)


def owned(connection, name):
    hold = screen_saver.ScreenHold('Slideshow')
    hold.hold()
    GLib.timeout_add(300, lambda: hold.release() and False)


Gio.bus_own_name(Gio.BusType.SESSION, 'org.freedesktop.portal.Desktop',
                 Gio.BusNameOwnerFlags.NONE, acquired, owned, None)
GLib.timeout_add(5000, loop.quit)
loop.run()
print('calls:', [call[2] for call in seen], flush=True)
os._exit(0 if [call[2] for call in seen] == ['Inhibit', 'Close'] else 1)
