---
type: Technique
title: A cold page turn
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-19T21:25:50+02:00" }
---

- (at 06ab4e28) STATE/probes/test_zz_cold_turn.py opens big60.cbz and, as soon as page 1 is available, jumps to pages the extractor has not reached, timing each until available.  At 06ab4e28: first page 71 ms after the window was built, page 50 with 2 of 60 extracted 45 ms.
