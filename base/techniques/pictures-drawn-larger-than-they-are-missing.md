---
type: Technique
title: "Pictures drawn larger than they are: missing, locked, CONTAIN"
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-24T07:34:02+02:00" }
---

- **Three ways a small picture got enlarged into a blur, all found at 478b5981-d002c0e0**: the main window laid the missing-page picture out at the 24 pixels it was read at (478b5981); the padlock cover was drawn at 64 and the library scales covers from 500 (2f336b39); and every Gtk.Picture left at CONTAIN - its default - enlarges its paintable to the room it has, which drew the test archive's 3 by 3 pages 27 times over in the thumbnail bar (0cba8675). A picture that stands in for something (missing, locked) is drawn at the size it is shown at; a thumbnail is shown with SCALE_DOWN.
- **The code-level sweep misses the widgets**: grepping for scale_up=True, keep_ratio=False and scale_simple finds only the page zoom and the library cover; the Gtk.Picture enlargement is in no MComix call. STATE/probes/picture_upscale.py walks every mapped Gtk.Picture and prints paintable size, widget size, content fit and the factor; the test archive 01-ZIP-Normal.zip, whose pages are 3 by 3, makes any enlargement obvious. Build the probe test class on its own: importing MainWindowTest into the probe module made pytest run all 327 of its tests.
- **The missing picture is known by a mark, not by identity**: image_tools.missing_image_icon() sets MISSING_IMAGE on every pixbuf it hands out and is_missing_image() reads it; an `is` test against the default size fails once the eight-entry cache has moved on.
