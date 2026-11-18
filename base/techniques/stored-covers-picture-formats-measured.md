---
type: Technique
title: "Stored covers: picture formats measured (PNG, WebP, AVIF, JPEG, JXL)"
tags: [code, performance]
sources:
  - { resource: "repo:mcomix/thumbnail_tools.py" }
generated: { by: mcomix-loop/claude, at: "2026-11-17T15:58:35+01:00" }
---

- **Probes**: `STATE/probes/bench_cover_formats.py <out dir> <pictures...>` (size, encode, decode per format, covers fit in 500 px; adds 4 synthetic comic-like covers; `AVIF_DEC=aom|dav1d`, `AVIF_THREADS`), `cover_quality.py <pictures...>` (PSNR at 500, 250, 125 px), `cover_formats_box.py` with `BOX=500|1000` (size, encode, decode, PSNR at one box). Run from the probes directory's parent with `python3 -I`; inputs used 2026-11-17: /usr/share/rofi/themes/iggy.jpg, /usr/share/gutenprint/samples/profile.jpg, /usr/share/backgrounds/sway/Sway_Wallpaper_Blue_768x1024_Portrait.png, docs/images/mcomix-mainwindow.png, docs/images/mcomix-continuous.png. Unreadable inputs are skipped.
- **Medians, Pillow 13.0 (webp 1.6.0, avif 1.4.2), one thread, 500 px box**: PNG level 6 198 kB, encode 13.4 ms, decode 2.2 ms; WebP q90 43.5 kB, 11.1 ms, 1.88 ms, PSNR 33.5 dB (min 29.8); WebP q80 34 kB; WebP lossless 166 kB, 68 ms; AVIF q75 4:4:4 31.2 kB, 63 ms (29.6 at speed 8), 2.4 ms, 37.3 dB; AVIF q75 4:2:0 29.5 kB, 33.1 dB; JPEG q90 4:4:4 74 kB, 0.7 ms decode, 36.9 dB; JPEG q90 4:2:0 57.5 kB, 32.5 dB. JXL: no Pillow codec; cjxl/djxl give lossless 161 kB decoding in about 29 ms, d1 52 kB in 3.5 ms.
- **1000 px box (a 2x screen at Huge)**: PNG 699 kB, 56 ms, 8.3 ms; WebP q90 125 kB, 37 ms, 5.8 ms, 37.0 dB; AVIF q75 4:4:4 87 kB, 435 ms (112 at speed 8), 7.8-8.3 ms, 39.0 dB.
- **WebP lossy is always 4:2:0** in Pillow: q95 only buys 33.9 dB for 54 kB; colour edges soften at 1:1, not at the drawn 250 px and below (39.0 / 44.6 dB).
- **The AVIF threads trap**: Pillow decodes AVIF with `AvifImagePlugin.DEFAULT_MAX_THREADS` (0 = the CPU count, 24 here): a 500 px cover then takes 15-19 ms with dav1d, against 2.3-2.9 ms on one thread. There is no per-open option; the encoder takes `max_threads`. Pillow 11.3 is the first with AVIF.
- **Which store may change**: the shared freedesktop store must stay PNG (spec; other programs read it, by Thumb::URI and Thumb::MTime tEXt). The library's private store (constants.LIBRARY_COVERS_PATH) may change; its metadata is tEXt today (Thumb::URI, Thumb::MTime, Thumb::Image::Width/Height, X-MComix::Orientation, X-MComix::Upright) and needs another carrier in WebP (XMP or EXIF chunk). The sized store (raw pixels, keep_sized) is the hot path and stays raw.
- **Built (2026-11-17)**: the library store is WebP q90 since 09c598f6 (XMP namespace urn:x-mcomix:thumbnail:1:, keys "Thumb.URI" for tEXt "Thumb::URI"; `thumbnail_tools._info_of_xmp()` reads them back; Pillow 10.1.0 keeps XMP in WebP too) and as large as the screen draws the Huge size since d1b6bd6d. A test that compares a library cover's exact colour fails on WebP: compare to within a few steps (ChosenCoverTest._page_coloured).
