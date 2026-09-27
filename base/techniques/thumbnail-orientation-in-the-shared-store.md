---
type: Technique
title: Thumbnail orientation in the shared store
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-23T22:17:54+02:00" }
---

- **What other programs store**: `/usr/share/thumbnailers/` lists the desktop's thumbnailers; GNOME's for JPEG/PNG here is `glycin-thumbnailer --input <uri> --output <png> --size <n>`. Run it on test/files/images/*-exif-* and compare with `ImageOps.exif_transpose()` of the source (mean of `ImageChops.difference`): it stores upright and writes no tEXt keys at all, so a thumbnail with no Software key is someone else's.
- **What MComix stores since 477b90e8**: upright, with `X-MComix::Upright` = 1 and, for archive covers, `X-MComix::Orientation`. `image_tools.UPRIGHT` on a pixbuf means upright; `turned_as_shown()` leaves it where 'auto rotate from exif' is on and turns it back where it is off. A thumbnail stored by an older MComix (Software "MComix ...", no Upright key) is as in the file and is turned where the preference is on.
