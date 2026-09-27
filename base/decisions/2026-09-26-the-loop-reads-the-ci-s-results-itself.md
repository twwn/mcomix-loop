---
type: Ruling
title: "The loop reads the CI's results itself"
tags: [installation]
generated: { by: claude.ai/claude-opus-5.5, at: "2026-09-27T12:00:00Z" }
---

"Let the loop read the CI's results itself" - after a push, the loop reads the GitHub Actions runs and the release with `gh` (reading only; the technique "The GitHub CI: reading its results, reproducing its jobs" has the commands) instead of waiting for the user's report. Pushing, tagging and anything else that reaches GitHub stay the user's.
