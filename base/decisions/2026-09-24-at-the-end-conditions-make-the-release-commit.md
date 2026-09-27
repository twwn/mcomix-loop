---
type: Ruling
title: "At the end conditions, make the release commit"
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-09-24T00:00:00Z" }
---

When the loop's end conditions are reached - no leads, no coverage gaps - it makes the CalVer release commit (`project.md`, `docs/releasing.md`). "No gaps" means nothing a test can reach in-process on Linux; Windows-only code, process start-up and the PDF worker processes are not waited for (at 9ae7ae41).
