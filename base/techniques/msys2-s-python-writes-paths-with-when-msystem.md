---
type: Technique
title: "MSYS2's Python writes paths with / when MSYSTEM is set"
tags: [windows]
sources:
  - { resource: "repo:.github/workflows/windows-tests.yml" }
generated: { by: mcomix-loop/claude, at: "2026-09-27T05:16:46+02:00" }
---

mingw-w64-python in MSYS2 sets os.sep to "/" when the MSYSTEM environment variable is set, as it is in every msys2-shell step of a GitHub workflow; without it os.sep is "\". MComix.exe never sees MSYSTEM. (corrected at aaff4733) `env -u MSYSTEM` inside an msys2-shell step does NOT help: the second CI run's workers still reported "D:/a/_temp/msys64/ucrt64/bin/python.exe" and the same path failures. windows-tests.yml now runs pytest from a `shell: pwsh` step with `$env:RUNNER_TEMP\msys64\ucrt64\bin` put first on PATH, and asserts os.sep == '\' before the suite. (corrected at 54fbf667) A pwsh step is not enough by itself: setup-msys2 exports MSYSTEM to every later step through the job environment, so the step first runs `Remove-Item Env:MSYSTEM`; the assert stopped the run at aaff4733 with "D:/a/_temp/msys64/ucrt64/bin/python.exe '/'". A workflow step's commands can be checked here with pwsh from a .ps1 file (quoting through bash eats the inner single quotes). Only MSYSTEM matters: MSYSTEM_PREFIX, MINGW_PREFIX, MSYSTEM_CHOST, MSYSTEM_CARCH, MINGW_CHOST and MINGW_PACKAGE_PREFIX each leave os.sep a backslash under Wine. Checked under Wine with the same python3.exe: `MSYSTEM=UCRT64` prints '/' and 'a/b'; unset prints '\\' and 'a\\b'. About thirty failures of the first Windows run were paths joined with "/" compared with GLib's backslashed ones.
