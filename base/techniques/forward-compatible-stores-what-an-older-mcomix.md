---
type: Technique
title: "Forward-compatible stores: what an older MComix reads"
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- **Forward-compatible stores**: the bookmarks pickle is read by older MComix as exactly two objects (version record, list of 6-tuples fed to `_Bookmark(*pack)`), so a new field goes in a third record, never into the tuple - one field more made the old reader drop every bookmark. The library database is relabelled with the older build's DB_VERSION when an older MComix opens it (its upgrade range is empty), so every upgrade step must be safe to run on a file that already has its change: check `pragma table_info` before `alter table add column`. Older code inserts with explicit column lists (`INSERT OR REPLACE INTO recent (book, page, time_set)`), so a new nullable column is left NULL by it rather than breaking it.
