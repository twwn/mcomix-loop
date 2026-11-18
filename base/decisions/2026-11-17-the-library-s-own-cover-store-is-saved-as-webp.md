---
type: Ruling
title: "The library's own cover store is saved as WebP or AVIF, whichever serves better"
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-11-17T14:58:02Z" }
---

"WebP or AVIF — consider your recommendation unbound by Pillow version" (2026-11-17, asked whether the library cover store should leave PNG) - the library cover store, private to MComix, moves from PNG to WebP or AVIF, picked on size, quality, encode and decode cost; requiring a newer Pillow is acceptable for it. The shared freedesktop thumbnail store is not covered: the spec requires PNG there.
