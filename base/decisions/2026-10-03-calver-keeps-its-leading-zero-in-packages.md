---
type: Ruling
title: CalVer keeps its leading zero in packages
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-10-03T10:06:08Z" }
---

"The python -m installer (or maybe the earlier build step) have the same CalVer leading-zero-lost issue - example: 26.09 turns to 26.9 - found for the release file names in an earlier commit." (at 9eb48112) - built and installed packages keep the version as VERSION writes it, 26.09, not 26.9.
