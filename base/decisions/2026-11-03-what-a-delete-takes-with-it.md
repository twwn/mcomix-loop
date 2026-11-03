---
type: Ruling
title: What a delete takes with it
tags: [program]
generated: { by: mcomix-loop/audit, at: "2026-11-03T17:03:09Z" }
replaces: [2026-09-21-what-a-delete-takes-with-it]
---

A delete takes the file off the disk, with its library entry and recent-files entry, unasked. Bookmarks are asked about first, in the window and the library, by one remembered prompt that defaults to keeping them; a book nobody bookmarked is not asked about, and books whose file would not go keep their bookmarks (5ee79c84, 59f23a30).
