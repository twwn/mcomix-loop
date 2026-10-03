---
type: Technique
title: The file chooser in a test
tags: [gtk]
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-03T05:04:42Z" }
---

- **`Gtk.FileChooserWidget.set_file()` given a folder clears the filter** (`get_filter()` is None once `get_file()` answers the folder; a file keeps it, and `set_current_folder()` keeps it). A test that chooses a folder under a filter sets the filter after the folder has settled (test_file_chooser, 5d6ab51e). Whether a reader's click on a folder row does the same was not probed.
- **A GTK file chooser destroyed before the main loop turns once shows GTK's "The folder contents could not be displayed" dialog**, over any folder. One pump before destroying is enough.
- **The file chooser's preview follows the chooser's selection, not `_previewed`.** A 200 ms poll compares `filechooser.get_file()` with `_previewed` and clears the preview when nothing is selected, so a probe that sets `_previewed` and calls `_update_preview()` by hand is undone within a fifth of a second and reports a cleared preview whatever the code does. Select with `widgets.set_chooser_file(dialog.filechooser, path)` and wait for the poll instead.
- **A file created after a Gtk.FileChooser listed its folder cannot be selected with set_file() until the chooser notices it**; write every file a chooser test selects before the chooser opens, or the second selection silently keeps the first.
- (at 123e4254) **Wait for the file you asked for, not for any file**: `set_file()` into a folder the chooser has not listed moves there first, and on GitHub's Windows runner the folder's first file ended up selected (the preview then said "1x1 px" for blue.png). FileChooserTest._select() sets the file and waits until `widgets.chooser_paths()` is exactly `[path]`. A Save chooser's file is its folder plus the typed name: set them apart (`set_chooser_folder`, `set_current_name`) and assert the wait (c83499f7).
