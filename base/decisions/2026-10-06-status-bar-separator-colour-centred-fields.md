---
type: Ruling
title: "Status bar separator colour, centred fields, double-page join"
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-10-06T19:49:23Z" }
---

"I don't actually prefer the line made stronger, but colorwise more visible in the three themes"; "Centre every field"; "also replace the \", \" separator of dual-page mode with something else (or nothing at all, whatever you deem best)" (at 43a971a8, after "Ah, pause. The current separator is also a | - like but barely visible in dark mode") - replaces the ruling of 2026-10-06 "Status bar separators and centred fields": the fields stay parted by GTK separator lines, not a "|" glyph, drawn in a colour that shows in the light, dark and black schemes (1ea5212f); the text of every field is centred (fc876084); a double page's two values are joined by " · " (d25518ce).
