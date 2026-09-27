---
type: Technique
title: A Gtk.Entry in a dialog selects all of itself
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-20T13:37:36+02:00" }
---

- An entry that takes the focus as its dialog is shown has the whole of its text selected, whatever was selected before: `select_region()` called while the dialog is being built is undone by the time the reader sees it. Pick the part out afterwards - `GLib.idle_add()` with a handler that selects and returns `GLib.SOURCE_REMOVE` is enough, since the idle runs after the dialog has been presented (a986339e's neighbour, 6d7911ba, is the worked example: a rename entry that offers the name with everything but the extension picked out).
- `Gtk.Editable.get_selection_bounds()` answers `(start, end)` in PyGObject, not the `(bool, start, end)` the C signature suggests.
