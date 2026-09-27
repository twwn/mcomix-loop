---
type: Ruling
title: "Exif-rotated thumbnails turn when drawn, not when stored"
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-09-22T00:00:00Z" }
---

A thumbnail of a page with an Exif rotation is turned as the page is, following `auto rotate from exif`, when it is drawn (7f1c143e); what goes into the shared freedesktop cache, which other programs read, is stored upright (477b90e8). Library covers are turned by Exif too (7b9bc937).
