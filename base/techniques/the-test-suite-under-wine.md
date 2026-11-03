---
type: Technique
title: The test suite under Wine
tags: [windows]
sources:
  - { resource: "repo:mcomix/portability.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-11-03T14:50:00Z" }
---

Runs pytest with MSYS2's UCRT64 python3.exe under Wine, on an export of HEAD in STATE/scratch/wine/tree (`rm -rf tree; mkdir tree; git archive HEAD | tar -x -C tree`, then copy changed files in). It needs the MSYS2 tree STATE/probes/wine_windows_build.sh unpacks (scratch/wine/msys/root) and pure-Python pytest, _pytest, pluggy, iniconfig, pygments copied from the host's site-packages into scratch/wine/pylib (PYTHONPATH). Run it as `env -u WAYLAND_DISPLAY timeout -k 5 60 xvfb-run -a STATE/probes/wine_pytest.sh test/<file>.py -q -p no:warnings > out.txt` and grep the file.

- It reproduces the Windows CI for what the CI runs without MSYSTEM: the cp1252 decoding errors, WinError 32 on open files, drive-letter paths, the CSD title bar, the Windows branches of portability.py. Checked on eleven CI failures that failed under Wine before a fix and passed after.
- **wineserver -k before each run** (the script does it): a wineserver left from an earlier xvfb display makes Gtk.init fail in the next run ("Gtk couldn't be initialized").
- **GDK_BACKEND unset, not empty**: an empty GDK_BACKEND also stops GTK initialising.
- **No PYTHONUTF8**: Windows runs in the ANSI code page (cp1252 on the runner, and in the de_DE Wine prefix), which is what finds the encoding bugs.
- **Set PYTHONUNBUFFERED=1 first when runs stall** (at 52549440): runs stalling at the limit with no pytest output, on two small files: 7 of 8 without it, 0 of 4 with it, in one session. Python and Gtk.init_check() alone ran fine meanwhile. Too few to say why, and an earlier session saw stalls with it set ("Windows: what the tests must not assume"). In zsh `$flags` does not split: exit 4 is pytest refusing "-q -s" as one argument.
- **Not faithful everywhere**: some chooser tests fail in teardown with WinError 145 (rmtree timing), the prefix has no 7z and no SVG loader, test_windows_build and test_pdf_multi (worker processes) hang, and a whole large file overruns 60 s. Trust Wine for a failure that matches the CI log; an extra Wine-only failure is not evidence. Without 7z, test_archives.py under Wine fails 26 tests that unpack a nested .7z or a tar.xz through 7z (RecursiveArchiveFormat*RedAndBlues, 7zExternalTarXz); the runner passes them. (corrected at 7a139017)
- **Copy UnRAR64.dll in before a change to a RAR handler** (at 7a139017): without it every RarDll test skips, so Wine says nothing about them, and 9bb28a35 passed here and then failed 16 tests on the CI. win32/fetch_unrar.ps1's DLL is at scratch/unrar-fetch/out; copied to scratch/wine/msys/root/ucrt64/bin (WINEPATH) it loads, and `-k "RarDll and Glob"` then reproduced the CI's 16 exactly. Rebuild the MSYS2 tree and it has to go in again.
- **A fix can fail the suite by being right** (at 7a139017): test_archives' expected failures are strict, so a handler change that cures one shows as "Unexpected success". Before calling a change to a handler done, read `xfail_list` for what it might cure, the block for `win32` too, which this machine never runs.
- **The prefix's user folders were links into the real home** (Desktop, Documents, Downloads, Music, Pictures, Videos -> /home/<user>/...). They were replaced with empty directories at 17788a60; a new prefix has them again, and must be treated the same before anything runs in it.
