---
type: Technique
title: Screenshots under Xvfb
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-24T12:25:08+02:00" }
---

- (at 7945e6ac) **A screenshot of a window under Xvfb**: inside a test (MComixTest), present the window, wait for what should be drawn (`wait_for(lambda: False, seconds=2)` lets frames pass), then `subprocess.run(['import', '-window', 'root', path])` (ImageMagick) and `magick path -crop WxH+0+0 crop.png` to read it. Give xvfb-run `-s "-screen 0 1280x900x24"`. Call `theme.follow_theme()` first: the tests never install MComix's stylesheets (run.py does, at startup), so without it a screenshot shows none of MComix' own styling. Gtk.WidgetPaintable of a window that is not yet drawn snapshots to None; test_theme's helpers poll until it does not, and walk the render nodes (a CSS outline is a BORDER_NODE).
- **A class on a widget is not a style on screen**: the picked-out outline was tested by its CSS class for months while its rule was never loaded under libadwaita with the system scheme (fffd332b). Assert what is drawn - the render nodes, or a screenshot - for any feature whose whole point is how it looks.
- **Screenshots for docs/images**: `STATE/probes/screenshots.py <outdir>` under `xvfb-run -a -s '-screen 0 1920x1080x24'`, from the checkout, about 15 s; it opens test/files/pepper-and-carrot at pages 2-3 and files it in the library. View the PNGs before replacing the committed ones.
- **Shrinking the screenshots:** `pngquant --speed 1 <name>.png` writes `<name>-fs8.png`, a 256-colour palette image; move it over the original, since the pages link the images by name.  At 186de239 it took mcomix-mainwindow.png (1280x800, painted comic pages) from 1,083,626 to 386,294 bytes, the library from 17,172 to 5,899 and the external commands dialog from 40,548 to 14,299.  Checked with PIL and numpy against the original: mean absolute channel difference 1.4 on the main window (99th percentile 13, all in the dithered art), 0.006 and 0.018 on the dialogs; a 2x nearest-neighbour crop of both side by side showed no difference.
