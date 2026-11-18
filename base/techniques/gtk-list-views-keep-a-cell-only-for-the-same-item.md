---
type: Technique
title: "GTK list views keep a cell only for the same item object, and their scroll anchor with it"
tags: [gtk]
sources:
  - { resource: "repo:mcomix/thumbnail_list.py" }
  - { resource: "repo:mcomix/library/book_area.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-11-17T17:10:00Z" }
---

- (at 76479468, GTK 4.24.1) **A Gtk.GridView or ListView keeps a cell over items-changed only for the very GObject it showed before.** Replacing 400 entries with new ThumbnailItem objects for the same uids in one `splice(0, n, items)` cost 321 setups and 321 unbinds; the same objects cost none and 1.2 ms; half of them the same, 161. The order of the splice does not matter, the identity does. STATE/probes/test_zz_grid_splice_reuse.py counts it (patch `_ThumbnailViewBase._setup_cell` on the class before the view is built: the factory connects bound methods when it is made, so patching an instance afterwards counts nothing).
- **A kept cell is not bound again.** Whatever the view does at bind (asking for a missing thumbnail, re-making a stale one, recording the position) does not happen for an entry shown again. thumbnail_list.set_items() therefore keeps `_stale` for entries shown again, asks again the orders it cleared for entries still bound, and rereads `_bound` positions from `cell.position`.
- **The scroll anchor is an item too.** After a splice that keeps objects, GTK scrolls to keep the anchored entry where it was, even if `adjustment.set_value(0)` ran just before the splice. A reversed order then ended at the bottom, and a search cleared, which brought books back before the first shown, opened 508 px down. `view.scroll_to(0, Gtk.ListScrollFlags.NONE, None)` after the splice holds the top. In a test, a jump made right after such a splice is undone at the next layout: settle first, then jump.
- **Gtk.MultiSelection keeps an entry selected across a splice that removes and re-adds the same object.** Clear the selection first if "nothing is selected in what was just shown" is the rule.
