---
type: Technique
title: "HiDPI: GDK_SCALE=2 under Xvfb gives a surface of scale 2"
tags: [gtk]
sources:
  - { resource: "repo:mcomix/main.py" }
  - { resource: "repo:mcomix/page_image.py" }
  - { resource: "repo:mcomix/thumbnail_list.py" }
  - { resource: "repo:mcomix/library/book_area.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-17T04:31:17Z" }
---

- (at 0d384ac1) **A 200 per cent screen in a test**: run under the X11 backend with `GDK_SCALE=2` in the environment (`env -u WAYLAND_DISPLAY GDK_BACKEND=x11 GDK_SCALE=2 xvfb-run ...`); `window.get_surface().get_scale()` is then 2.0 and `get_scale_factor()` 2. It is read when the display opens, so it is process-wide: a test of one scale among others patches `MainWindow.device_scale` instead (test/test_hidpi.py), and a probe is a test_zz_ file run on its own with the variable set.
- **What to read**: a page drawn at a scale above 1 is a fixed-size paintable (page_image._AnimationPaintable) whose intrinsic size is the layout box and whose `_texture` has the screen's pixels: at 2, a box 297 wide over a texture 594 wide. At 1 the page is a plain Gdk.Texture of the box's size, as before 0d384ac1.
- **Not yet HiDPI** (at 0d384ac1): the thumbnail bar (thumbbar.py, generated at preview.scaled(prefs['thumbnail size'])), the library covers, the lens, and the previews; each is drawn in the window's pixels and enlarged by GTK.
- (corrected at cfb9bfde) The sidebar (c318cbf7), the library covers (f3b6278b), the archive editor (4c107fa4) and the lens (1aff2bc8) are now made with the screen's pixels as well. The thumbnail view carries `device_scale`, records on each item the scale its thumbnail was made at, and `thumbnail_list._shown()` draws one made above 1 through `_Scaled`, whose intrinsic size is the texture's divided by it. The library reads its own window's surface (book_area._device_scale), set on 'realize'; the editor reads the main window's once. What is left in the window's pixels: the file chooser preview (already scaled), the page selector's preview, the properties thumbnail, the about logo.
- **A test of a cover needs pages larger than the cover**: the test archives' pages are one to five pixels, and neither thumbnails nor the sidebar scale up, so a 2x test there sees a five-pixel texture. The Pepper&Carrot book (test/files/pepper-and-carrot) has 800-pixel pages; library covers do scale up (fit_in_rectangle scale_up=True), so the one-pixel archive serves there.
