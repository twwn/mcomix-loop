---
type: Technique
title: "Double page turns, traced"
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-22T23:01:51+02:00" }
---

- STATE/probes/test_zz_double_page_trail.py builds books from N (portrait PNG), W (landscape PNG), J (portrait JPEG) and R (landscape by Exif) pages, as a directory and as an archive, turns forward to the end and back, and prints what is shown at each turn ("1+2 >3 >4 <3 <1+2").  At bdc4b7bd no layout showed a wide page paired with a narrow one.  Going back does pair differently from going forward: directory NNNWWN shows 1+2, 3 forward and 2+3, 1+2 back.
- (at 94dbb87c) **Pairing in double page mode is a property of the run since the last wide page.**  A wide page always stands alone, so the first page and every wide page start a spread whatever came before; between them all pages are narrow and pair two by two (after the title page in an archive).  `ImageHandler.spread_start()` uses that, and `MainWindow._previous_spread()` turns back onto it unless the spread would reach into the pages on screen.  The trail probe with `SAME/DIFF` post-processing (compare the back trail with the forward trail reversed) checked 22 books; keep the layout list from 94dbb87c's message when changing any of this.  Walking the book page by page without a width cache cost 7.4 ms per turn back at page 59 of big60.cbz; the closed form and the per-path width memory cost 0.22.
