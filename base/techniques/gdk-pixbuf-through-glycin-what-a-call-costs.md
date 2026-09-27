---
type: Technique
title: "gdk-pixbuf through glycin: what a call costs"
tags: [code]
sources:
  - { resource: "repo:mcomix/animation.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- **gdk-pixbuf does not decode in the calling process where glycin is installed**: glycin decodes in a helper process and hands each frame back through shared memory (`memfd_create("glycin-frame")`). Its cost is per call, so it dominates at thumbnail size and per animation frame, and profiling that reads only `RUSAGE_SELF` misses most of it (about 8x). Measured 2026-08-30 on a 1080x1920 30 fps animated WebP: `PixbufAnimationIter.advance()` 33 ms wall for 4 ms of CPU in the caller, Pillow 9 ms, ffmpeg 9.3 ms - which is why animated pages decode with Pillow (`mcomix/animation.py`) and keep the iterator as a fallback. `GLYCIN_SANDBOX_MECHANISM` makes no difference; `Gtk.MediaFile` cannot play animated WebP at all here (playbin3: "Internal data stream error").
- **Where gdk-pixbuf's loaders are sandboxed (glycin), any gdk-pixbuf call that touches a file costs about as much as decoding it** — `Pixbuf.get_file_info()` included. A PIL header read is about 190 times cheaper.
- Full-size decoding gains nothing from PIL over glycin (1200x1800 JPEG 5.1 ms by gdk-pixbuf, 5.4 ms by PIL; a 3 MiB JPEG 37.4 against 36.9; a PNG 37.5 against 78.5): glycin's cost is per call, which only dominates at thumbnail size.  SCRATCH/thumbbench/full.py measured it.
- **STATE/probes/bench_thumb_decode.py** times a 128x128 scaled decode three ways in one process: `GdkPixbuf.Pixbuf.new_from_file_at_size`, Pillow `Image.draft()` plus `pil_to_pixbuf` and `fit_in_rectangle`, and `image_tools.load_pixbuf_size` as it stands (gdk-pixbuf first). It writes its test images under SCRATCH/thumbbench.
- Here, with glycin: a 1200x1800 68 KiB JPEG 8.9-10.9 ms by gdk-pixbuf against 0.8 ms by Pillow; a 1988x3056 3 MiB JPEG 48 ms against 18.8; a 1988x3056 14 MiB PNG 49 ms against 85 (draft() does nothing for a PNG, so Pillow decodes the whole picture and then scales it). `load_pixbuf_size` tracks the gdk-pixbuf column.  The Windows build has no glycin, so the gdk-pixbuf figures there would differ; measure before claiming anything about it.
- (at 44950202) **glycin converts embedded ICC profiles into sRGB; PIL does not.**  Before routing any decode from gdk-pixbuf to PIL, compare colours on a JPEG carrying a non-sRGB profile (Ghostscript ships /usr/share/ghostscript/iccprofiles/a98.icc, ps_rgb.icc, esrgb.icc): SCRATCH/thumbbench/icc.py style, flat red (200, 30, 30) saved with `icc_profile=`, read back through both.  Adobe RGB red is (233, 24,
  24) through glycin and (200, 30, 30) through raw PIL. `image_tools._in_srgb()` converts with ImageCms and matches glycin exactly for all three.  1001052c missed this and 44950202 fixed it.
- Neither decoder's orientation survives `fit_in_rectangle()` scaling: it returns a new pixbuf.  `load_pixbuf_size` now carries the orientation across.  Thumbnails are not rotated by it anywhere (get_implied_rotation is read only for pages).
- The 60-page benchmark, SCRATCH/thumbbench/bar.py (saved as STATE/probes/bench_thumb_bar.py), makes big60.cbz's thumbnails at 128x128 through `Thumbnailer(store_on_disk=False)`: 447-450 ms at 2956aee6, 53 ms at 1001052c and 44950202.
