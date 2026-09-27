---
type: Ruling
title: No hard wrapping of Markdown prose
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-09-26T00:00:00Z" }
---

The wrapping "isn't necessary anymore and rather disadvantageous": ChangeLog.md entries, release notes, `docs/*.md` and README keep each paragraph or list entry on one line (a sentence per line is fine); GitHub release notes keep every line break, so a wrapped section comes out ragged (unwrapped in aff56bb4). Commit messages keep the usual git wrapping.
