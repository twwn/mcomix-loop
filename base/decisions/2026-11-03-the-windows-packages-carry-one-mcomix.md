---
type: Ruling
title: "The Windows packages carry one MComix executable, without a console"
tags: [program]
generated: { by: mcomix-loop/audit, at: "2026-11-03T17:03:09Z" }
replaces: [2026-09-26-the-windows-build-ships-mcomix-exe-alone]
---

One MComix executable, MComix.exe, without a console (ce231aab): `MComix.exe -W debug -o mcomix.log` writes what a console would show, so MComix.Console.exe does not come back. Helpers it needs, such as 7z.exe and JxrDecApp.exe, are not meant by this.
