---
type: Iteration Notes
---
## Gate numbers as of 6db038e9 (seed from another installation; re-baseline)

    pytest -n 8     3666 passed, 12 xfailed (2381 subtests), 26.2-28.0 s,
                    56-59 warnings
    floors venv     3491 passed, 8 skipped, -n 4, 35.5 s (at 8a0f4352)
    flake8 -F       silent
    mypy mcomix     no issues in 161 source files
    catalogues      24 of them, 669 translated messages each, none fuzzy
    deprecations    16 names; the 2 asyncio ones filtered (754140ea)
    library schema  DB_VERSION 10 (recent.member, cf0b7e48)
    prefs format    CONFIG_FORMAT_VERSION 4 (8e4c6fa1)
    Linux CI        at c4d6d959: 1 failure, 3.12 only (fixed 1c42d6e4);
                    "invalid (NULL) class pointer" 0 in all three jobs
    Windows CI      at 12d00721: green, 755 s; one-file step 219
                    passed in 161 s. Log: logs_98334836687

Quiet iterations: 0

## Campaign

None open.

## Questions for the user

None.

## What the last iteration changed

Nothing on this installation yet. The gate numbers above are that checkout's. Re-baseline the gates on a clean tree, then rewrite this file as your own.

## Leads worth picking up

None.

## Prompt corrections

None.
