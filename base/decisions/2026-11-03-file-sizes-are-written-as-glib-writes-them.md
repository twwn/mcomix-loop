---
type: Ruling
title: File sizes are written as GLib writes them
tags: [program]
generated: { by: mcomix-loop/audit, at: "2026-11-03T17:03:09Z" }
replaces: [2026-09-24-the-preview-size]
---

File sizes are written as GLib.format_size() writes them, in decimal units, so that the file chooser's preview and the list beside it agree (0b272df4).
