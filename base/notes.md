---
type: Iteration Notes
---
## Gate numbers as of 7f3a46f6 (seed from another installation; re-baseline)

    pytest -n 8     3693 passed, 12 xfailed (2393 subtests), 16.4-17.2 s, ~53 warnings
    catalogues      24 x 676 messages, none fuzzy
    flake8 -F       silent
    mypy mcomix     no issues in 161 source files
    one file, one process (test_main_window.py -p no:xdist): 0.065/0.059/0.062/0.060 s a test by quarter, 13.5 s of test time, 0 main windows alive (since 8ae02e62)
    not re-measured here (seed, at 6db038e9): floors venv 3491 passed; 24 catalogues x 669 messages, none fuzzy; 16 deprecation names; DB_VERSION 10; CONFIG_FORMAT_VERSION 4
    GitHub CI at b227b832: Windows suite 151.7 s, one-file 0.29-0.30 s flat, job 6.3 min; a second Windows run failed in the chooser preview test (fixed 123e4254); Pages green

Quiet iterations: 0

## Campaign

None open.

## Questions for the user

None.

## What the last iteration changed

Nothing on this installation yet. These notes were seeded from another installation; the gate numbers above are that checkout's, and the leads below were true there. Re-baseline the gates on a clean tree, then rewrite this file as your own.

## Leads worth picking up

1. After the user's next push: read the Windows run (now on push) - suite time against 151.7 s with the campaign landed, the one-file quarters, and whether the one-file step still warns g_filename_to_uri (5507d079); the chooser tests' new waits (123e4254) and the edit dialog's (c83499f7) on both runners.
2. Feature requests 6-29 (ruling 2026-10-03; 1-5 done, marked DONE in features.md; the preferences dialog was reorganised in da26e8f1 - new options go to the tab their section names), small ones first, one commit each; re-read each item's whole ticket in STATE/scratch/sf/all.json first (`python3 STATE/scratch/sf/show.py STATE/scratch/sf feature-requests/<n>`). The first change to the preferences dialog (items 4, 12, 18) starts with a review of its tabs, Behaviour first.
3. SourceForge leftovers: open patches (7), support requests (14), forum topics (29); STATE/scratch/sf/triage.md.
4. gtk_box_remove criticals (six at once) when a file chooser test is torn down after a long wait - seen in both CI chooser failures and here in a forced failure; find which box.

## Prompt corrections

None.
