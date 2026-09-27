---
type: Technique
title: "Which thread reaches something, across the whole suite"
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- **A pytest plugin on PYTHONPATH answers "can a thread other than the main one ever do X" better than reading call sites.**  Install the patch in `pytest_runtest_setup` the first time it runs, not in `pytest_configure`: by then the test modules have imported mcomix the way they mean to, and importing it earlier from a plugin risks resolving the constants against the real home.  Write what it sees to a file per pid (xdist workers load `-p` plugins too), count the main-thread hits as well so an empty result is shown to be a working probe, and run it on an export: `PYTHONPATH=<scratchpad> xvfb-run -a python3 -m pytest test/ -n 8 -p <module>`. It showed 876 library backend openings or requests with none open, every one on the main thread.
- **Patch a module-level factory, not a name bound at import.** `backend.LibraryBackend` is looked up at call time by every caller (`get_backend()` imports it inside the function), so replacing the module attribute reaches them all.
