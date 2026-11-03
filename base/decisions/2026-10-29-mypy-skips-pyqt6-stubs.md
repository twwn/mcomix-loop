---
type: Ruling
title: mypy skips PyQt6 stubs
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-10-29T22:56:59Z" }
---

"Yes, skip the stubs" (at fcfdc92e, on PyQt6 6.12 stubs breaking mypy here) - pyproject.toml tells mypy to skip PyQt6 modules (follow_imports = skip); MComix does not use PyQt6.
