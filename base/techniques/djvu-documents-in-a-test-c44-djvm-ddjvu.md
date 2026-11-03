---
type: Technique
title: "DjVu documents in a test: c44, djvm, ddjvu"
tags: [testing]
sources:
  - { resource: "repo:mcomix/archive/djvu_external.py" }
  - { resource: "repo:test/test_djvu_external.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-10T00:04:36Z" }
---

- (at d5738931) **A DjVu document is written in a test, not kept in test/files**: Pillow saves a PPM, `c44 page.ppm page.djvu` makes a one-page document, `djvm -c book.djvu page1.djvu page2.djvu` bundles several. All three come with DjVuLibre (Arch: djvulibre; Ubuntu: djvulibre-bin, installed in tests.yml). test/test_djvu_external.py _write_djvu() does it and skips where c44, djvm or ddjvu are missing; MSYS2's Windows job has none, so there only NoDjVuLibreTest runs.
- **What the tools answer**: `djvused -e n book.djvu` prints the page count; `ddjvu -format=tiff -page=N in out.tif` draws page N at the document's own resolution (a 40x60 page comes out 40x60). Neither takes "--". A bundled document starts AT&TFORM....DJVM, a single page AT&TFORM....DJVU.
