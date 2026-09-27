---
type: Technique
title: "The Windows build: PyInstaller, Wine and pwsh on Linux"
tags: [windows]
sources:
  - { resource: "repo:win32/mcomix.spec" }
  - { resource: "repo:win32/build_pyinstaller.py" }
  - { resource: "repo:mcomix/run.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-26T10:15:48+02:00" }
---

- **What is in a release zip, and why**: `zipfile` over it by top-level directory and by file size; then which bundled DLL imports which, with `pefile` (pip, in a scratch venv) reading each DLL's import and delay-import tables. At 26.09 that showed GStreamer imported by libgtk-4-1.dll itself (needed), the AV1 codecs by libavif (Pillow's and gdk-pixbuf's AVIF), OpenSSL by Python's _ssl/_hashlib alone, and mutool.exe by nothing. A theme icon's presence: search the name in the bundle's files and in libgtk-4-1.dll/libadwaita-1-0.dll's bytes (their compiled-in resources); grep here is ugrep with colour, so use Python.
- **PyInstaller's gi hooks default to GTK 3.0**: without `hooksconfig={'gi': {'module-versions': {'Gtk': '4.0', ...}}}` the Gtk hook finds no GTK 3 and returns, collecting no icon theme, no gtk40.mo, no Windows font configuration - silently. `languages` limits every gi translation domain; `icons` names themes; filter `a.datas` in the spec for what a hook over-collects (Adwaita's X11 cursors).
- **The spec builds on Linux**: `pip install pyinstaller` in a `--system-site-packages` venv, then `python -m PyInstaller win32/mcomix.spec --distpath <scratch> --workpath <scratch>` from the top of the checkout; only the Windows-only settings (version file, icon) go unused. The frozen app then runs under xvfb-run with HOME and every XDG_* variable pointed at a scratch folder - a fresh process takes its paths from the environment, unlike an in-process probe - and `-W debug -o <log>` plus its stdout/stderr say what failed. That found the missing freeze_support() ("unrecognized arguments: -B -S -I -c" on a PDF) and the missing gi._gi_cairo/cairo ("Couldn't find foreign struct converter for 'cairo.Context'", with a book that is not there, which makes the on-screen display draw). The spec tests stand in for Analysis/EXE/COLLECT with recorders (test_windows_build SpecDataTest).
- **The workflows cannot run here**: actionlint (binary from its GitHub release) checks syntax and expressions; PowerShell steps are extracted with PyYAML and parsed with `[System.Management.Automation.Language.Parser]::ParseFile` under pwsh; network lookups a step makes (RARLAB's UnRAR.dll) can be run on their own under pwsh. The release workflow's own test build (run by hand with no tag) is the check of the Windows job.

Decisions of the user done by bd1f979a, moved out of the notes:
- **PowerShell Core is installed as `pwsh`**, so the scripts under `win32/tools/` need not be changed blind: parse-check with `[System.Management.Automation.Language.Parser]::ParseFile(path, [ref]$tokens, [ref]$errors)`, and drive one by defining a stub for the Chocolatey helper it calls before dot-sourcing it (`Install-ChocolateyPackage` takes the splatted hashtable as *named* parameters, so the stub needs those names).
- **STATE/probes/wine_windows_build.sh <workdir>** builds the checkout's HEAD for Windows and starts it: it resolves the UCRT64 package closure from repo.msys2.org's ucrt64.db (STATE/probes/msys2_resolve.py; 130 packages, 228 MB), unpacks them (no pacman needed), writes the pacman database pacman would have (the build reads it for licences), compiles GLib's schemas, runs MSYS2's python3.exe on win32/build_pyinstaller.py under Wine (about 70 s), then runs dist/MComix/MComix.exe on a PDF with `-W debug -o` and takes a screenshot. No MSI (WiX needs .NET).
- **Put the workdir under STATE/scratch** (home filesystem): the tmpfs /tmp filled up once mid-run (~1.8 GB per workdir), and the guard allows recursive rm under STATE/scratch only.
- **Use a scratch WINEPREFIX**, never ~/.wine: MComix' settings land in the prefix's AppData. `winepath -w` converts paths; zsh's echo turns "\t" in "Z:\tmp" into a tab. GSK_RENDERER=cairo avoids Wine's GL.
- **Unset WINEPATH before running the bundle**, so a DLL missing from it shows instead of being found in the MSYS2 tree.
- **A frozen build's tracebacks show today's source**: Python finds "mcomix/run.py" relative to the working directory, so an old build run from the checkout prints the current file's lines.
- Found this way: the 26.09 draft's zip had no Gtk/Gdk/Gsk-4.0 typelib and did not start ("Namespace Gtk not available"), the same GTK-3 default of PyInstaller's gi hooks as 51bb1925; the fixed build opens a PDF and draws every toolbar icon.
