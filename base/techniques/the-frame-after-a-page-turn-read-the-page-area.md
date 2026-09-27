---
type: Technique
title: "The frame after a page turn: read the page area, not the scroll bars"
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-23T21:01:37+02:00" }
---

- **The scroll bars hold the page turned from until the page area is next allocated**, a frame after `_draw_image()` has called `set_content_size()` and `scroll_to()`. Anything that reads a position or bounds in that frame reads the old page: `PageCanvas.get_position()` answers with what `scroll_to()` asked for until the allocation applies it, and `get_content_size()` with the new size. `MainWindow.scroll()` and `update_layout_position()` use those since c7b0f542; `scroll_offset()` still reads the adjustments on purpose, because it maps a pointer onto what is drawn. A new reader of `_hadjust` / `_vadjust` that acts on the view (rather than on what is on screen) belongs with the first group.
- **To put a key press in that frame deterministically**, press the key that turns the page and then call `window._draw_image()` directly, instead of pumping: `pump()` can let the frame clock tick under load, and a precondition "the frame has not come yet" then failed in 20 to 28 of 48 copies (24 of each of two tests) per run under `-n 8` with coverage. With the direct call it held in 288 of 288. `test_key_press._ScrollablePageTest._draw_without_a_frame()` does it and asserts `page_area._wanted is not None`.
- test/files/images as a book, opened at portrait-no-exif.png and zoomed eight steps, has page 22 (840 by 1188) followed by red.png (100 by 100), smaller: Space to the end of 22 then Shift+Space, or Down to the end, three presses, then Up three times, goes back to a larger page at its end.
