---
type: Technique
title: "Start-up import time: -X importtime, and what is left"
tags: [code]
sources:
  - { resource: "repo:mcomix/main.py" }
  - { resource: "repo:mcomix/i18n.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-29T22:30:00Z" }
---

- **Measure:** `timeout -k 5 60 python3 -X importtime -c "import mcomix.main" 2> <SCRATCH>/importtime.txt`, then `sort -t'|' -k2 -n -r` on it: the second column is cumulative microseconds. For a before/after number take the best of five runs of the `| mcomix.main` line (`awk -F'|' '{print $2+0}' | sort -n | head -1`); single runs vary by about 10 ms here.
- **An exclusive cost** is not the cumulative column: a module whose children the main window imports anyway saves only its own part. Import those children first, then time the module with `time.perf_counter()` around its import in the same `-c` (the library's main_dialog: 31 ms cumulative, 8.5 ms exclusive at 79658019).
- **At 79658019 (134 ms best of five):** gi with asyncio (about 30 ms; PyGObject's gi.events imports asyncio, not MComix), Gdk and Gtk typelibs (about 31 ms), image_tools with PIL, archive_tools with the PDF and native PDF modules and concurrent.futures. chardet (28.7 ms) was moved to first use in 79658019; the library window (8.5 ms exclusive) was left (rejected.md).
- **A test that holds a lazy import** runs a child Python under a temporary HOME, APPDATA, LOCALAPPDATA and XDG_* (constants.py resolves paths at import) with `cwd` the checkout, and reads `'<module>' in sys.modules` after `import mcomix.main` (test_i18n.py StartUpImportTest).
