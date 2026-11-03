---
type: Ruling
title: "The folder walk skips folders with no book, within a border"
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-10-03T11:55:03Z" }
---

"Yes, Page Down/Up should skip such folders — but not infinitely, a sane default resp. border is required. For instance, how about no movement that does up/down two levels in the folder hierarchy? Critically review this. (Shouldn't this movement ough to occur with all keys bound to it, not just Page Down/Up?)" (at 252cc9e8) - the walk past a book's end passes over folders with no book instead of opening them empty, within a bound; the bound (levels, anchor) is still to be settled after the loop's review, and the same walk applies to every key that leaves a book.
