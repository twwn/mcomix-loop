---
type: Technique
title: Probes
tags: [testing]
sources:
  - { resource: "repo:mcomix/constants.py" }
  - { resource: "repo:test/__init__.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- **`MComixTest` is the base class for any ad-hoc script.** `mcomix/constants.py` resolves `CONFIG_DIR`, `DATA_DIR` and about ten derived paths **at import time**, so setting `HOME` and the `XDG_*` variables is not enough; the constants have to be reassigned, and `test/__init__.py` already does it correctly. Getting this wrong has destroyed a preferences file, the keybindings and the bookmarks (a bare script building a `MainWindow` writes them all on `terminate_program()`) and leaked test files into the reader's recently-used list. Run one with `unittest.main(argv=[sys.argv[0], 'Probe'])` and then `os._exit(0)`: leaving the GTK main loop does not end the process, because MComix' worker threads are not daemons, and `os._exit` does not flush, so flush stdout first.
- **`Gtk.RecentManager.get_default()` writes to `~/.local/share/recently-used.xbel`.** Patch `get_default` to return a `Gtk.RecentManager(filename=<temp>)`.
- **A GUI probe must destroy its windows.** A dialog left on screen is answered by the next test that goes looking for one, which shows up only in a full-suite run.
- **Distrust the probe before the code.** Findings that were the probe being wrong: reading `get_action_area()` on a dialog that keeps its buttons elsewhere; `AccelLabel.get_accel()`, which reports only manually set accelerators and so said "none" for a menu with 72; classifying every model-built menu item as a checkbox because they all derive from `GtkCheckMenuItem`.
- STATE/probes/probe_library_leak.py closed the library with `main_dialog._close_dialog()`, which skips `_LibraryDialog.close()` and with it `book_area.close()`; every real path goes through `close()`.
- STATE/probes/probe_editor_leak.py counted the main window sidebar's ThumbnailItems with the editor's and its page wait returned at once; STATE/probes/verify/probe_editor_leak2.py takes the tree as a parameter, waits on the grid's store and counts the editor's items apart.
- **A probe module that imports a TestCase subclass under its own name runs all of that class's tests** (pytest collects it); import it under an underscore name, subclass it, and set the unwanted test methods to None on the subclass. Deleting the imported name with `del` breaks a subclass method that calls the base's.
- **A pytest plugin patching `tools.atomic_write` to log a stack for any path under the real `~/.local/share/mcomix`** finds a test writing to the reader's home. The suite's own output says nothing about it. Worth re-running whenever a test opens a `MainWindow`.
