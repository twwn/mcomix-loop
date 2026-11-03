---
type: Ruling
title: How two pages are swapped
tags: [program]
generated: { by: mcomix-loop/audit, at: "2026-11-03T17:03:09Z" }
replaces: [2026-09-21-the-swap-gesture-and-its-mark]
---

CTRL+SHIFT and a click, on a page or its thumbnail, marks that page with a dashed outline; the next such click swaps the two, and clicking the marked page again unmarks it. The same keys drag one page onto the other, in double page mode or among the thumbnails; a drag that ends anywhere else changes nothing (f28db1de, ec97e760, 10fac538).
