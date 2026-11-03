---
type: Ruling
title: The folder walk stops at the shelf
tags: [program]
generated: { by: mcomix-loop/audit, at: "2026-11-03T17:03:09Z" }
replaces: [2026-10-03-the-folder-walk-s-border-is-the-shelf, 2026-10-03-the-folder-walk-skips-folders-with-no-book]
---

"I confirm the shelf limit" (at 252cc9e8) - every key that leaves a book walks on past its end, passing over folders with no book. The shelf is the parent of the folder of the book opened by hand; the walk goes depth-first in natural order over the shelf's subfolders down to two levels below it, never climbs above the shelf, never descends through a symlinked folder, the same both ways.
