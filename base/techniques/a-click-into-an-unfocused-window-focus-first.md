---
type: Technique
title: "A click into an unfocused window: focus first, flag cleared from idle"
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-23T21:14:57+02:00" }
---

- **The order is: focus, press, idle, release.** `gained_focus()` clears `was_out_of_focus` from the idle queue, which runs after the press has been handled and before the release arrives. So the press sees the flag and the release does not; anything the release must know about a raising click has to be handed over by the press (`EventHandler._raising_click` since c1a50f96). A handler that returns early on the flag must still record whatever a later event measures from - the press position was skipped, and the release and the first drag motion measured from the previous click's.
- **To reproduce in a test**: `window.lost_focus(); window.gained_focus()`, then the press, `self._pump()` (runs the idle), then the release or a motion (test_main_window `_refocus()`, `_Click`, `_Motion`). `_click()` returns the point it clicked, so a second click can land on the same spot, which is what exposed the page turn.
