---
type: Ruling
title: "The folder walk's border is the shelf"
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-10-03T11:58:39Z" }
---

"I confirm the shelf limit" (at 252cc9e8, on the proposal in the notes) - the shelf is the parent of the folder of the book opened by hand; the walk goes depth-first in natural order over the shelf's subfolders down to two levels below it, skips folders without books, never climbs above the shelf, never descends through a symlinked folder, the same both ways.
