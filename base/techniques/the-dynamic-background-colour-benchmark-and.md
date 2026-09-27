---
type: Technique
title: "The dynamic background colour: benchmark and test page"
tags: [code]
sources:
  - { resource: "repo:test/test_background_colour.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-19T20:53:39+02:00" }
---

- (at ebc12ff4) STATE/probes/bench_edge_colour.py times `image_tools.get_most_common_edge_colour()` against any MComix tree (first argument; `git archive HEAD mcomix | tar -x -C <dir>` gives the old one) on the images named after it, median of 30 calls.  The test pages big60.cbz holds have too few colours to exercise the grouping; a noisy scan does: 1200x1800 RGB, `random.seed(1)`, every pixel (232, 228, 215) plus `randint(-6, 6)` per channel, clamped.
- A page one pixel wide makes both edges the same column, so a test can set the exact colour counts the function sees (EdgeColourTest).
- (at 78569057) The colour is read by `MainWindow._edge_colour()` off the pixbufs as drawn (turned, flipped, scaled, enhanced), ordered by their content boxes' x. test/test_background_colour.py builds a 60x90 page with red sides and a blue top and bottom with PIL (small enough not to be scaled, so the colours stay exact); a quarter turn must read blue. To count work done inside one redraw, call `window._draw_image()` directly under the patch rather than pumping: the thumbnail sidebar enhances its thumbnails from the idle queue too, and the count then depends on timing (1 alone, 3 in a file run).
