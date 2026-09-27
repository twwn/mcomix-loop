---
type: Technique
title: "The Windows branches of portability.py, run on Linux"
tags: [windows]
generated: { by: mcomix-loop/claude, at: "2026-09-26T05:15:17+02:00" }
---

- Patch `sys.platform` to `'win32'` and `ctypes.windll` with `create=True` (it does not exist off Windows); a Mock's `kernel32.GetUserDefaultUILanguage.return_value` is the LANGID. test_portability `WindowsDefaultLocaleTest` does it.
- `locale.windows_locale` (423 entries in 3.14) lacks some Windows display languages: 0x0486 K'iche' and 0x0850 traditional Mongolian of the Windows 11 language packs checked. A lookup of a LANGID from Windows is `.get()`, never a subscript.
- `%APPDATA%` needs `ntpath.expandvars` patched over `os.path.expandvars` as well as the platform: posixpath's leaves `%VAR%` alone (test_tools `TestWindowsDirectories`, at 4971e936; test_openwith_command does the same for the command line).
