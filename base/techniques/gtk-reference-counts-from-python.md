---
type: Technique
title: "GTK reference counts, from Python"
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- **`obj.__grefcount__` reads a GObject's reference count**, so a bare GTK script can show whether a call balances its references: a count that turns to garbage (3545088429) means the object was freed while Python still holds it, and the next `gc.collect()` segfaults. GTK 4.22.5 with PyGObject 3.56.3: `Gtk.FileChooserWidget.remove_filter()` frees the filter it removes, current or not; add/remove of a CSS provider for the display balances. STATE/probes/probe_remove_filter.py.
- **A segfault in teardown under pytest shows as "Fatal Python error: Segmentation fault" and rc 139**, with the Python stack printed; the frame is often `tools.garbage_collect`, which only finds the damage. Bisect the setup in a probe on MComixTest with a `gc.collect()` between steps (STATE/probes/probe_libchooser.py).
