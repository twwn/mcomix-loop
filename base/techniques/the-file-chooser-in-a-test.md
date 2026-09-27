---
type: Technique
title: The file chooser in a test
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-25T03:09:28+02:00" }
---

- **`Gtk.FileChooserWidget.set_file()` given a folder clears the filter** (`get_filter()` is None once `get_file()` answers the folder; a file keeps it, and `set_current_folder()` keeps it). A test that chooses a folder under a filter sets the filter after the folder has settled (test_file_chooser, 5d6ab51e). Whether a reader's click on a folder row does the same was not probed.
- **A GTK file chooser destroyed before the main loop turns once shows GTK's "The folder contents could not be displayed" dialog**, over any folder. One pump before destroying is enough.
- **The file chooser's preview follows the chooser's selection, not `_previewed`.** A 200 ms poll compares `filechooser.get_file()` with `_previewed` and clears the preview when nothing is selected, so a probe that sets `_previewed` and calls `_update_preview()` by hand is undone within a fifth of a second and reports a cleared preview whatever the code does. Select with `widgets.set_chooser_file(dialog.filechooser, path)` and wait for the poll instead.
- **A file created after a Gtk.FileChooser listed its folder cannot be selected with set_file() until the chooser notices it**; write every file a chooser test selects before the chooser opens, or the second selection silently keeps the first.
