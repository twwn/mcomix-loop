---
type: Ruling
title: How renaming behaves
tags: [program]
generated: { by: mcomix-loop/audit, at: "2026-11-03T17:03:09Z" }
replaces: [2026-09-21-how-renaming-behaves]
---

A page is renamed from its menu or with F2, in the window and the archive editor. The name replaces the whole old one, and a name without an extension keeps the old extension. In an archive the name waits for the next save; in a folder of images the file is renamed at once, and a name a file that is not a page holds is refused. A name another page holds is flagged, with "Swap the names" and "Replace". No batch rename (6d7911ba, a986339e, 48793054, 3d852d50, be264545, 38fa1a0e).
