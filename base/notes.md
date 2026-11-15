---
type: Iteration Notes
---
## Gate numbers as of 49bd8551 (seed from another installation; re-baseline)

    pytest -n 8     4877 passed, 3 skipped, 20 xfailed, 59 warnings, 2902 subtests passed in 32.27s (at 49bd8551, re-run clean at the next iteration; test_edit_dialog right-click focus test failed once in a run at f8be1a79, passed on rerun: same family as lead 15; see lead 15 for the one flaky test; in the checkout; the third skip is test_screen_saver.WindowsTest, which passes under Wine; pytest 9.2 prints 'u' for a passed subtest; the second skip is TestDiskSpelling's drive-letter test, Windows only; warnings vary 54-62 with the per-worker asyncio notice and WaitGaveUp timing; the skip is CheckImportsTest's real-PE test, Windows only, passes under Wine). The 8 extra xfails are the RarDll glob extract tests under libunrar 7.3.2 (52e18c71). test/pytest.ini makes a DeprecationWarning attributed to an mcomix module an error (30fa9d89). Once (eaebbb2e + the test_ion edit) gates.sh pytest exited 1 with everything passed and no failure logged; two reruns clean; unattributed. One worker segfault in GTK's icon theme at 6674a854, once in four runs (technique "A worker that aborts inside GTK").
    floors venv     whole suite 4421 passed, 16 skipped, 20 xfailed at e62965cc (Pillow 10.1.0, PyGObject 3.46.0; STATE/scratch/floorsenv, CPython 3.12.14); touched tests re-run there at 4251e466 and at 4ef6f53d (test_image_tools FramesNotInTime, test_library_types, test_book_area) and test_tiff_archive.py at 64c75e22 (20 passed, 1 skipped: Pillow 10.1.0 writes no BigTIFF).
    catalogues      24, 805 translated each, none fuzzy (at f8be1a79)
    flake8 -F       silent (at 49bd8551)
    mypy mcomix     no issues in 175 source files (at 49bd8551) (PIL.ImageQt not followed: PyQt6 6.12 stubs do not parse)
    deprecations    15 names reached (at 840d5c6d; the listing's 16th line, "The", is pytest-asyncio's)
    coverage        96% of 19844 statements, 767 missed (at 4196a9f6); gaps are guards (rejected.md)
    import time     mcomix.main 133.9 ms best, 138.2 median of 15 (at aed6ed4a)
    Windows start   a Wine build of d4f93fd5 loads 116 of its files, 91.1 MB of 191.7, by "Started" (124 and 159.3 MB before; technique "The Windows build"). Bundle 196 MB unpacked, 1268 files; zip 96.3 MB.
    Windows imports 167 PE files of a Wine build of 63e5d0b1 import 145 DLL names, 0 unresolved (win32/check_imports.py since b3796180; technique "The Windows build").
    code scanning   1 open on 2026-11-10: alert 16, Scorecard PinnedDependenciesID at docs.yml:72, the docs job's unpinned test install rejected.md already holds (as docs.yml:70; the line moved, the alert got a new number). The user's to dismiss.
    CONFIG_FORMAT_VERSION 12; DB_VERSION 12
Quiet iterations: 0

## Campaign

None open.

## Questions for the user

None.

## What the last iteration changed

Nothing on this installation yet. These notes were seeded from another installation; the gate numbers above are that checkout's, and the leads below were true there. Re-baseline the gates on a clean tree, then rewrite this file as your own.

## Leads worth picking up

15. test_collection_area.py test_a_right_click_moves_the_keyboard_focus_too still fails about one full run in four under eight workers: at dc096966 + 6a2227e1 its second assertion failed, "2 != 1" (after the click the focus stayed on Comics for 5 s). The first assertion's failure ("1 != -1") is fixed by dc096966. The cause is unknown: the scroll_to(FOCUS) request after the click seems to be dropped under load. A real bug would show as Enter acting on the wrong row; read collection_area.py:416 and column_list.select_and_focus with that in mind before touching the test again.
16. Issue 72: Go back and Go forward over the pages a jump left (peers lead). Small, but it needs two actions, keys, menu entries, docs and 24 catalogues.
17. archive_packer.py:394 (windows lead, unproven): saving as 7z or RAR stages each file under its archive name; a name holding ':' or a device name names an NTFS stream or device. Wine on ext4 cannot show it (STATE/scratch/sweep/windows/test_staged_colon.py printed LINK OK). The extractor's sanitiser (archive_base.py:232-258) is not used there.
18. relocate_dialog.py:105 (windows lead, unproven): the folders are compared case-sensitively (backend.py:670-680), so on Windows "d:\comics" for "D:\Comics" relocates nothing, and a new folder typed in another case than the disk's makes the books count as others later (file_handler.py:490 opens them under tools.disk_spelling()).
14. Thumbnails still asked for every bound cell, ~32 rows' worth, not only those near the viewport; only with a reason.
1. Sweeps: a new installation has no sweeps.log, so every lens is due when the leads run out. Fable only where the user names it (sweep.md); Xvfb as technique "Probes" says, which the guard enforces.
4. Windows start-up, what is left: 116 files, 91.1 MB still load before the window shows; libgtk-4-1.dll and what it imports are most of it, the AV1 codecs 22.7 MB (rejected.md). Real numbers need Windows: under Wine only loaded files and the phases after "Building the main window" mean anything. Signing (lead 9) is what stops Smart App Control checking each file.
5. Chapters, what is left: pdf_external.py (mutool) lists no outline; KFX's of_book call passes no chapters (kfx.py ~1040; needs the clean-room description, ruling 2026-11-03). No key or menu entry for next/previous chapter. Only with a reason.
6. Pinch zoom keeps the view's middle; the gesture's bounding-box centre could anchor it as c8b38b5b anchors the wheel. Small; only with a real touchpad check.
7. Scheduled runs: Monday 2026-11-09's all succeeded. A fuzzing failure's input is artifact crashes-<target>: fix, add to fuzz/regressions/<target>/. Flatpak updates: read `gh api repos/twwn/mcomix/check-runs/<job id>/annotations` for the beta's notice.
8. KFX PDF pages (09c255f6): the $46-$50 margins are ignored; only with a real print-replica sample.
9. SignPath wiring, once the user has the organisation.
10. Keep STATE/scratch/sf/changelog.md current: 80 entries, through 73a94962 (docs and test commits get no line).
11. RAR symlink members: RAR 5 and Windows' DLL were not probed (rejected.md); only with a reason.
12. filehandler.wait_for_files() before a save waits on the main thread without the dialog; only with a measurement.
2. After the user pushes f8be1a79..49bd8551: read Windows tests first (43713797921 failed at 73a94962), then Tests and CodeQL; close nothing: no issue was finished.
19. Library sort, further keys only with a reason: format/type and reading progress (pages read of pages) were considered and not built in f8be1a79.

## Prompt corrections

None.
