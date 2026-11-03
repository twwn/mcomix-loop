---
type: Ruling
title: "A version keeps its leading zero, except in Python's own records"
tags: [program]
generated: { by: mcomix-loop/audit, at: "2026-11-03T17:03:09Z" }
replaces: [2026-10-03-calver-keeps-its-leading-zero-in-packages, 2026-10-03-the-calver-backend-is-dropped]
---

"Drop the CalVer backend." (at 2a144342) - the tag and the release files keep the version as `mcomix/constants.py` spells it, 26.09. Python's own records (the wheel, .dist-info, METADATA, PKG-INFO, PyPI) normalise it to 26.9, as the specifications ask, and no build backend respells them.
