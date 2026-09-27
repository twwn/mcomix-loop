---
type: Technique
title: The test suite under Wine
tags: [windows]
sources:
  - { resource: "repo:mcomix/portability.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-26T21:12:06+02:00" }
---

Runs pytest with MSYS2's UCRT64 python3.exe under Wine, on an export of HEAD in STATE/scratch/wine/tree (`rm -rf tree; mkdir tree; git archive HEAD | tar -x -C tree`, then copy changed files in). It needs the MSYS2 tree STATE/probes/wine_windows_build.sh unpacks (scratch/wine/msys/root) and pure-Python pytest, _pytest, pluggy, iniconfig, pygments copied from the host's site-packages into scratch/wine/pylib (PYTHONPATH). Run it as `env -u WAYLAND_DISPLAY timeout -k 5 60 xvfb-run -a STATE/probes/wine_pytest.sh test/<file>.py -q -p no:warnings > out.txt` and grep the file.

- It reproduces the Windows CI for what the CI runs without MSYSTEM: the cp1252 decoding errors, WinError 32 on open files, drive-letter paths, the CSD title bar, the Windows branches of portability.py. Checked on eleven CI failures that failed under Wine before a fix and passed after.
- **wineserver -k before each run** (the script does it): a wineserver left from an earlier xvfb display makes Gtk.init fail in the next run ("Gtk couldn't be initialized").
- **GDK_BACKEND unset, not empty**: an empty GDK_BACKEND also stops GTK initialising.
- **No PYTHONUTF8**: Windows runs in the ANSI code page (cp1252 on the runner, and in the de_DE Wine prefix), which is what finds the encoding bugs.
- **Not faithful everywhere**: some chooser tests fail in teardown with WinError 145 (rmtree timing), the prefix has no 7z and no SVG loader, test_windows_build and test_pdf_multi (worker processes) hang, and a whole large file overruns 60 s. Trust Wine for a failure that matches the CI log; an extra Wine-only failure is not evidence.
- **The prefix's user folders were links into the real home** (Desktop, Documents, Downloads, Music, Pictures, Videos -> /home/<user>/...). They were replaced with empty directories at 17788a60; a new prefix has them again, and must be treated the same before anything runs in it.
