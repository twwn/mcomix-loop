---
type: Technique
title: "The session bus in a test: a private daemon and a stand-in service"
tags: [testing]
sources:
  - { resource: "repo:mcomix/screen_saver.py" }
  - { resource: "repo:test/__init__.py" }
  - { resource: "repo:test/test_screen_saver.py" }
generated: { by: mcomix-loop/claude-fable-5-2, at: "2026-11-14T09:31:33Z" }
---

- (at e67afd09) **No test reaches the session bus.** `test/__init__.py` replaces `screen_saver._session_bus`, the one function that calls `Gio.bus_get`, with one that never answers; a slideshow started by any test would otherwise ask the desktop of whoever runs the suite to keep the screen on. New code that talks to the bus goes through a seam of the same kind, stubbed there.
- **A unit test hands the code a recording bus**: an object with `call(name, path, interface, method, parameters, reply_type, flags, timeout, cancellable, callback)` that stores the unpacked parameters and keeps the callback, `call_finish(result)` that returns a `GLib.Variant` or raises `GLib.Error`, and an `answer()` the test calls when the reply is to arrive. That makes the order of answer and release the test's to choose, which is where the bugs are (a release before the answer).
- **The wire format is proven once against a real daemon**, never the user's: `PYTHONPATH=$PWD PROBE_PRIVATE_BUS=1 timeout -k 5 60 env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -d dbus-run-session -- python3 -W ignore STATE/probes/screen_hold_bus.py` (Xvfb added 2026-11-15, as the guard now asks; same output). `dbus-run-session` starts a daemon of its own and sets `DBUS_SESSION_BUS_ADDRESS` for the child only. The probe owns `org.freedesktop.portal.Desktop` there (`Gio.bus_own_name`, `register_object` with a `Gio.DBusNodeInfo` from XML), runs the real code and prints what the stand-in received; it ends with `calls: ['Inhibit', 'Close']`. The probe refuses to start without `PROBE_PRIVATE_BUS=1`.
- A portal request is ended by `Close` on the request's object path (`org.freedesktop.portal.Request`), and by the portal itself when the caller leaves the bus, so nothing needs to run at quit.
- **Windows:** `SetThreadExecutionState()` answers with the state before the call, so a test reads the state by setting the released one (`0x80000000`) and looking at the answer. Wine keeps the state as Windows does; the test passes there.
