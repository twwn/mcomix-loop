---
type: Technique
title: A worker that aborts inside GTK
tags: [gtk]
sources:
  - { resource: "repo:test/test_library_dialog.py" }
  - { resource: "repo:test/test_main_window.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- **"worker 'gwN' crashed" with "Fatal Python error: Aborted"** and a C stack of `gtk_window_destroy` → `gtk_widget_unrealize` → `gsk_renderer_unrealize` → `g_assertion_message_expr` is a GSK renderer assertion under Xvfb, not MComix code. It took down `test_library_dialog.py::WatchListScanTest::test_closing_an_edited_watch_list_scans_the_library` once in four full runs at c9d0b9ce, and three runs of a clean export passed. The tests set no `GSK_RENDERER`. Record the stack and rerun on an export before blaming a change; the Python stack names only the line that destroyed a window.
- **Second sighting (2026-09-13):** the same C stack (`g_assertion_message_expr`, `gsk_renderer_unrealize`, `gtk_widget_unrealize`, `gtk_window_destroy`) aborted worker gw1 in `test_main_window.py::MainWindowTest::test_the_right_click_menu_saves_the_page_it_was_opened_over`, once in about 30 full runs that day, on a tree whose code four other runs passed.  Grep the pytest log for `gsk_renderer_unrealize` to tell it from a crash of MComix' own.
- **A segmentation fault in the icon theme (2026-11-03, at 6674a854, gtk4 4.24.1):** "worker 'gw3' crashed", "Fatal Python error: Segmentation fault", main thread, C stack `gtk_icon_theme_lookup_by_gicon` → `gtk_icon_theme_lookup_icon` → two unnamed frames in libgtk-4 (+0x16f37a, +0x16ec3e), under a layout, reached from `pump` in `test_file_chooser.py` setUp while the chooser first drew. No Python thread of MComix' was alive, only execnet's. Once in four full runs; the next three, and four runs of the file under `-n 8`, passed. gtk4 has no symbols here, so the frames stop there: `coredumpctl info <pid>` shows the same names. Grep the pytest log for `gtk_icon_theme_lookup` to tell it from a crash of MComix' own; a second sighting is the reason to go further.
