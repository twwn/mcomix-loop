---
type: Technique
title: Sorts that leave ties to the listing order
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-23T23:43:40+02:00" }
---

- **Every sort key needs a last resort.** A stable sort keeps tied items in the order they arrived, and that order is a file system's listing, an archive's, or a list model's insertion history: the same book or library then comes out differently from one copy or one showing to the next. The check: sort every permutation of a handful of tied inputs (`itertools.permutations`) and require one result. At 11addcd4-bccc2711 that found ties in the natural sort (case, leading zeros), sort_files by mtime and size, the archive's GLib order (basename only), and the library's covers (date added, size, name); each now falls back on the natural sort of the whole path.
