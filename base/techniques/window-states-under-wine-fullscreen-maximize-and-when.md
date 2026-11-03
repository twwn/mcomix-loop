---
type: Technique
title: "Window states under Wine: fullscreen, maximize, and when the notifications come"
tags: [windows]
sources:
  - { resource: "repo:mcomix/event.py" }
  - { resource: "repo:mcomix/main.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-17T12:00:00Z" }
---

The win32 backend of GDK manages maximize and fullscreen itself, so under Wine (unlike the bare Xvfb the suite runs on, which grants neither) both requests really take effect and their notifications really arrive. That makes Wine the place to watch a sequence of window states on the Windows code path.

- **probes/wine_fullscreen_maximized.py** is a test module: copy it into scratch/wine/tree/test/ as test_zz_fsmax.py and run it with probes/wine_pytest.sh under `xvfb-run -a -s "-screen 0 1280x1024x24"`. It builds a MainWindow, maximizes it, enters and leaves fullscreen through the action, wraps restore_window_geometry() and maximize(), and logs every notify::fullscreened, notify::maximized and default size change, with the state read at that moment, to fsmax.log in the tree. Its pump turns the default context for wall-clock seconds, since the state changes come through the Windows message queue.
- **What it showed at 4788b3b4** (GTK 4.24, MSYS2 UCRT64): entering fullscreen drops maximized (notify::maximized False before notify::fullscreened True). Leaving fullscreen sends notify::fullscreened while is_maximized() is still False and the size is still the screen's; GDK alone puts the window back at its unmaximized size and does not maximize it again. A maximize() called from inside that notification gave maximized True and then False at once, ending unmaximized at 1252x995; the same call from an idle gave one maximized True and ended at 1280x1024. Windows 11 crashed on the former (user report); the fix is 013b5fe4.
- **Wine's maximized size is the whole screen** (no task bar), so a comparison of the maximized size with the fullscreen size is equal there and unequal on Windows: a check that compares sizes behaves differently on the two.
- The first run after an earlier one in the same session hung once before pytest's header (exit 124, output only MESA lines); run it again, as "The test suite under Wine" says.
