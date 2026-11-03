---
type: Technique
title: "Counting redraws over a pump: late pages and resizes land there too"
tags: [testing]
sources:
  - { resource: "repo:test/test_main_window.py" }
  - { resource: "repo:mcomix/main.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-17T11:00:00Z" }
---

- (at d4967448) **A test that patches `draw_image` and then pumps the main loop counts every redraw the pump delivers, not only the one it means.** MainWindowTest's setUp() pumps until nothing is pending, which on a loaded runner is before the extractor has handed over a page; the page arriving later is redrawn by `_page_available` with `scroll_to=SCROLL_TO_START` (-3). Bars that come back shrink the page area, and `EventHandler.resize_event` redraws with no arguments. The Windows job met the first ([call(scroll_to=-3), call(), call(scroll_to=-3)]), and `-n 8` here met the second ([call(), call()]) once the first was waited out.
- **Count only what the code under test asks for**: wrap the callback itself on the instance before it is scheduled (`GLib.idle_add(self._restore_geometry_idle)` reads the instance attribute, so `patch.object(window, '_restore_geometry_idle', counted)` is what gets queued), slice `draw_image.call_args_list` before and after it runs, and assert that it ran at all, or an empty list passes for the wrong reason (`_draws_on_going_back` in test_main_window.py).
- **Reproducing a late page deterministically**: `STATE/probes/latepage_plugin.py` (`PYTHONPATH=<probes> pytest ... -p latepage_plugin`) holds every `Extractor._extract_file` until the test first calls `window_state_event` (or 0.5 s), and holds the main thread in `restore_window_geometry_soon` until a page has been extracted, so its arrival lands in the test's pump. It failed both fullscreen tests at 39c94110 three runs in three, as the CI did. A plain `time.sleep` in the extractor did not: the pump returns as soon as nothing is pending, so the arrival has to be made to land inside it. Wine did not reproduce it either (4 of 4 passed): the CI's failure came from load, not from Windows.
