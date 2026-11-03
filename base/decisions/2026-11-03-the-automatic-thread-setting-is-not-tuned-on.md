---
type: Ruling
title: The automatic thread setting is not tuned on one machine
tags: [program]
generated: { by: mcomix-loop/audit, at: "2026-11-03T17:03:09Z" }
replaces: [2026-10-03-thread-auto-setting-cpu-count-was-a-suggestion, 2026-10-03-thread-counts-default-to-the-available-cpus]
---

"That was a review suggestion, not a fixed ruling" (at b91ee04e) - both thread preferences default to an automatic setting that is not a number tuned on one machine and stays within what memory and processes allow. How it is computed is the loop's to settle by review and measurement; the CPU count is one candidate.
