---
type: Ruling
title: CI caching and docs-only skip
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-10-29T23:08:26Z" }
---

"1 and 2, also check whether such caching is relevant/possible for the Linux runners" (at c148dfc6) - windows-tests.yml skips docs-only pushes and caches the installed UCRT64 tree (package list + ISO week key); the Linux workflows are checked for the same.
