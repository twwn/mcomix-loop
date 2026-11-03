---
type: Iteration Notes
---
## Gate numbers as of 78870f1d (seed from another installation; re-baseline)

    pytest -n 8     4666 passed, 1 skipped, 20 xfailed, 57 warnings, 2861 subtests, 30.25 s (at 78870f1d's tree; the skip is CheckImportsTest's real-PE test, Windows only, passes under Wine). The 8 extra xfails are the RarDll glob extract tests under libunrar 7.3.2 (52e18c71). test/pytest.ini makes a DeprecationWarning attributed to an mcomix module an error (30fa9d89). Once (eaebbb2e + the test_ion edit) gates.sh pytest exited 1 with everything passed and no failure logged; two reruns clean; unattributed. One worker segfault in GTK's icon theme at 6674a854, once in four runs (technique "A worker that aborts inside GTK").
    floors venv     whole suite 4421 passed, 16 skipped, 20 xfailed at e62965cc (Pillow 10.1.0, PyGObject 3.46.0; STATE/scratch/floorsenv, CPython 3.12.14); touched tests re-run there at 4251e466.
    catalogues      24, 788 translated each, none fuzzy (at 60326c31)
    flake8 -F       silent (at 78870f1d)
    mypy mcomix     no issues in 170 source files (at 78870f1d) (PIL.ImageQt not followed: PyQt6 6.12 stubs do not parse)
    deprecations    15 names reached (at 840d5c6d; the listing's 16th line, "The", is pytest-asyncio's)
    coverage        96% of 19844 statements, 767 missed (at 4196a9f6); gaps are guards (rejected.md)
    import time     mcomix.main 133.9 ms best, 138.2 median of 15 (at aed6ed4a)
    Windows imports 167 PE files of a Wine build of 63e5d0b1 import 145 DLL names, 0 unresolved (win32/check_imports.py since b3796180; technique "The Windows build").
    code scanning   0 open on 2026-11-03 (read with gh api at 572e1de1)
    CONFIG_FORMAT_VERSION 12; DB_VERSION 12

Quiet iterations: 0

## Campaign

None open.

## Questions for the user

None.

## What the last iteration changed

Nothing on this installation yet. These notes were seeded from another installation; the gate numbers above are that checkout's, and the leads below were true there. Re-baseline the gates on a clean tree, then rewrite this file as your own.

## Leads worth picking up

0. After the next push, read the floors job (a repeat of test_library_dialog.py:777's wait means the cause was another) and the Windows run. Windows at 52549440 passed; one pass says little, since the failure came once in 19 runs. Watch test_kfx.py over the next runs; a further failure of test_the_folder_is_read_again_when_a_part_comes_or_goes means neither cause was the one, and the junit log's assertion line is where to start.
0a. The same drop in the program, bug, not started: thumbnail_list.redraw_item() goes through unique orders, so a redraw while that item's order is in flight is dropped (worker_thread.py:111) and the old picture stays until the item is next drawn; e739c0ab's message names it. BookArea._cover_changed is the caller a reader meets: another page chosen as cover while that cover is being made. Probe: park get_book_thumbnail as CoverInFlightTest does, call redraw_item twice, count the reads (expect 1, want 2). Small to medium; a fix must keep test_a_book_shown_again_does_not_have_its_cover_read_again.
1. Closing the library window still waits for the covers being read: main_dialog.close() calls book_area.stop_update(), which joins. With the slow 7z in flight it printed "stop_update(), as the library window closes: 5011 ms" (STATE/probes/test_zz_cover_typing.py -k closing, slow books as under "Re-check"). Not asked for and not started. A cure needs a stop without a join: WorkerThread._stop is shared and reset after the join, so a worker left running needs a stop of its own, and rejected.md's f0278684 line says why that was not needed for set_items(). The worker uses the backend, which outlives the window. Only a slow cover not yet stored shows it. Medium.
2. Flatpak updates on its next run (Monday 2026-11-09, or by hand): expect success and, while unrar's newest is a beta, the beta's notice. It is the first real test of bdd8bdfd. Newer releases now show only as a notice and in the summary, with no failure mail: read `gh api repos/twwn/mcomix/check-runs/<job id>/annotations` each Monday (technique "The GitHub CI") and report them; a security release of a module is worth a hand update of the manifest.
3. Monday's other scheduled runs: read them; a fuzzing failure's input is artifact crashes-<target> -> fix, add to fuzz/regressions/<target>/. windows-tests.yml has no schedule (grep finds none), so a new UnRAR.dll from RARLAB shows only on a push; Release's weekly run fetches the DLL but runs no tests.
5. Code scanning: 0 open at the push; unexplained for Branch-Protection since the classic rule is unchanged. A ruleset of the user's may explain it: read it before saying so.
6. User: cleanups, optimizations, feature amendments and new features, bug fixes (ruling 2026-10-30). No named amendment is left. The sweep of 60326c31 is finished; docs and windows lenses were not due then and come due with these commits.
7. KFX PDF pages (09c255f6): the $46-$50 margins are ignored; only with a real print-replica sample.
9. SignPath wiring, once the user has the organisation.
10. The page turn is done (single and double; rejected.md).
11. Keep STATE/scratch/sf/changelog.md current: 14 lines, through 52549440.
12. RAR symlink members, what is left: RAR 5 and Windows' DLL were not probed (rejected.md); only worth it with a reason.

## Prompt corrections

None.
