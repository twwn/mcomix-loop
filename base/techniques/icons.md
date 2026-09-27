---
type: Technique
title: Icons
tags: [gtk]
sources:
  - { resource: "repo:mcomix/ui.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-24T07:04:21+02:00" }
---

- **`Gtk.Button.set_icon_name()` replaces the button's child** with a new image of the default size; the tool bar's buttons carry a Gtk.Image at `Gtk.IconSize.LARGE`, so change that image instead.
- **Which theme answers for an icon**: `Gtk.IconTheme.get_for_display(d).lookup_icon(name, None, 16, 1, Gtk.TextDirection.LTR, 0).get_file().get_path()`. Adwaita ships only symbolic icons; a name without "-symbolic" is answered by AdwaitaLegacy in full colour, or not at all where that theme is not installed. Only the tool bar reads the icons ui.py names (`_actions.icon()`); the menus show none.
- **A symbolic icon loaded as a pixbuf keeps the colour its file was drawn in** (Adwaita: #2e3436), because the recolouring is GTK's, done for the widget the icon stands in. `icons.load_pixbuf()` of a `-symbolic` name composited onto an image all but vanishes on a dark one; use its alpha channel as a mask and pick the colours yourself (book_area `_finished_mark`, 56a90b24). `icons.load_pixbuf()` reads an SVG through gdk-pixbuf: about 5 ms each call, so load once, never per item (1f8e522b). GTK 4's icon theme allows lookups from worker threads once it is set up.
- **The picture for an image that would not load** is `mcomix/images/missing-image.svg`, rendered by `image_tools.missing_image_icon(width, height)` at the size shown (lru_cache of eight sizes; 4-25 ms the first time per size through glycin, at 39b6d6fb). Ask for the size you draw at rather than scaling it up. Without an SVG loader the fallback theme icon can be an SVG too (Adwaita's is), so `icons.load_pixbuf()` raises GLib.Error there as well. Where a pixbuf's size is compared in a test, crop `pixbuf_to_pil(...)`: `pixbuf_to_pil()` of `new_subpixbuf(...).copy()` on RGBA raises "buffer is not large enough" (the copy keeps the parent's stride and leaves the last row unpadded).
- **Checking a picture by eye**: `rsvg-convert -h 400 -b black x.svg -o out.png`, or save what the code draws (add_border and all) with `pixbuf_to_pil(...).save()`, composite it on the view's background with PIL, and Read the PNG.
