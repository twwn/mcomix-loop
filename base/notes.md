---
type: Iteration Notes
---
## Gate numbers as of 216804dc (seed from another installation; re-baseline)

    pytest -n 8     4741 passed, 2 skipped, 20 xfailed, 63 warnings (at 216804dc; the second skip is TestDiskSpelling's drive-letter test, Windows only; warnings vary 54-62 with the per-worker asyncio notice and WaitGaveUp timing; the skip is CheckImportsTest's real-PE test, Windows only, passes under Wine). The 8 extra xfails are the RarDll glob extract tests under libunrar 7.3.2 (52e18c71). test/pytest.ini makes a DeprecationWarning attributed to an mcomix module an error (30fa9d89). Once (eaebbb2e + the test_ion edit) gates.sh pytest exited 1 with everything passed and no failure logged; two reruns clean; unattributed. One worker segfault in GTK's icon theme at 6674a854, once in four runs (technique "A worker that aborts inside GTK").
    floors venv     whole suite 4421 passed, 16 skipped, 20 xfailed at e62965cc (Pillow 10.1.0, PyGObject 3.46.0; STATE/scratch/floorsenv, CPython 3.12.14); touched tests re-run there at 4251e466.
    catalogues      24, 790 translated each, none fuzzy (at ccd7d87f)
    flake8 -F       silent (at 216804dc)
    mypy mcomix     no issues in 172 source files (at 216804dc) (PIL.ImageQt not followed: PyQt6 6.12 stubs do not parse)
    deprecations    15 names reached (at 840d5c6d; the listing's 16th line, "The", is pytest-asyncio's)
    coverage        96% of 19844 statements, 767 missed (at 4196a9f6); gaps are guards (rejected.md)
    import time     mcomix.main 133.9 ms best, 138.2 median of 15 (at aed6ed4a)
    Windows imports 167 PE files of a Wine build of 63e5d0b1 import 145 DLL names, 0 unresolved (win32/check_imports.py since b3796180; technique "The Windows build").
    code scanning   0 open on 2026-11-07 (read with gh api at ad0dea08)
    CONFIG_FORMAT_VERSION 12; DB_VERSION 12

Quiet iterations: 0

## Campaign

None open.

## Questions for the user

None.

## What the last iteration changed

Nothing on this installation yet. These notes were seeded from another installation; the gate numbers above are that checkout's, and the leads below were true there. Re-baseline the gates on a clean tree, then rewrite this file as your own.

## Leads worth picking up

0. After the next push (seven commits), read Tests, Windows tests, CodeQL. A second gtk_box_remove segfault is the reason to chase it: find the worker's previous test. Watch test_kfx.py on Windows (one failure in 19 runs before 52549440), test_save_progress.py there too; the new Windows-path tests (held_open in test_tools/test_archive_packer/test_thumbnail_tools, utf8 in test_tools, the library delete in test_book_area) run for real there for the first time.
1. Windows path case is done in 216804dc; entries already kept twice under two spellings are not merged (only with a reason).
2. Chapters, what is left: pdf_external.py (mutool, used without PyMuPDF) lists no outline; KFX's of_book call passes no chapters (kfx.py ~1040; its navigation would need the clean-room description, ruling 2026-11-03). A key or menu entry for next/previous chapter does not exist. Only with a reason.
3. Pinch zoom keeps the view's middle; the gesture's bounding-box centre could anchor it as c8b38b5b anchors the wheel. Small; only with a real touchpad check.
4. Flatpak updates on its next run (Monday 2026-11-09, or by hand): expect success and, while unrar's newest is a beta, the beta's notice. Read `gh api repos/twwn/mcomix/check-runs/<job id>/annotations`.
5. Monday's other scheduled runs: a fuzzing failure's input is artifact crashes-<target>: fix, add to fuzz/regressions/<target>/ (fuzz_epub now reaches the nav and NCX parsing).
6. Code scanning: 0 open on 2026-11-06; unexplained for Branch-Protection since the classic rule is unchanged. A ruleset of the user's may explain it: read it before saying so.
7. KFX PDF pages (09c255f6): the $46-$50 margins are ignored; only with a real print-replica sample.
8. SignPath wiring, once the user has the organisation.
9. Keep STATE/scratch/sf/changelog.md current: 47 lines, through 216804dc.
10. RAR symlink members: RAR 5 and Windows' DLL were not probed (rejected.md); only with a reason.
11. filehandler.wait_for_files() before a save waits on the main thread without the dialog; only with a measurement.

## Prompt corrections

None.
