---
type: Technique
title: "GTK list focus moves only in the active window; xdist workers share one Xvfb"
tags: [gtk, testing]
sources:
  - { resource: "repo:mcomix/widgets.py" }
  - { resource: "repo:test/__init__.py" }
generated: { by: mcomix-loop/claude, at: "2026-11-17T15:58:35+01:00" }
---

- **`scroll_to(pos, Gtk.ListScrollFlags.FOCUS)` grabs widget focus only when the list has `GTK_STATE_FLAG_FOCUS_WITHIN`**, and GTK sets that flag only while the window is active. In a window that is not active, the list's focus-tracker item moves but the keyboard focus stays on the cell focused before, so Enter afterwards acts on that one. `list.grab_focus()` moves the focus to the focus-tracker item. `widgets.focus_where_scrolled(view)` (1a5aa827) does that where the focus was inside the view already.
- **The eight pytest-xdist workers share one Xvfb display**, and a window one worker presents takes activation from another worker's. A test that depends on its window being active fails about one full run in two (the right-click focus family: test_book_area, test_collection_area, test_edit_dialog, before 1a5aa827). To test the inactive case on purpose: `test.take_activation_from(self, window)` in test/__init__.py presents a window of its own, destroys it in a cleanup, and waits until `window.is_active()` is false.
- **Proving it**: STATE/scratch probes are gone; rebuild as a MComixTest that right-clicks a cell after take_activation_from() and reads `window.get_focus()` against the clicked cell.
