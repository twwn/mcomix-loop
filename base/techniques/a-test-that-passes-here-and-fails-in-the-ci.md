---
type: Technique
title: "A test that passes here and fails in the CI: floors, Windows, a slower runner"
tags: [testing]
sources:
  - { resource: "repo:.github/workflows/tests.yml" }
  - { resource: "repo:.github/workflows/windows-tests.yml" }
  - { resource: "repo:test/__init__.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-11-17T18:40:00Z" }
---

- **How often, and why** (counted at e982e39f from `git log --since=2026-10-01`, 538 commits): about 35 commits fixed a test or the build after a failure seen only in the CI. Three kinds, each a check the gates do not make. (1) **The floors** (PyGObject 3.46, old GTK/GLib/Python): bc9c4b5e, 5de90e7a and e982e39f are the same trap three times, `Gtk.Snapshot.to_node()` under PyGObject 3.46; also 05620f39 (GTK 4.14), 1368363a (GLib 2.80), c193f33d (Python 3.15). (2) **The Windows runner**: b3f5b505 (seven new tests at once), 6b4dba97, 7a139017, 978725ce, 8ab5c421, a59d940e, and lead 36's four at 8b7b313f; Wine reproduced some and not others (it passed lead 36's three shelf tests). (3) **A slower runner**: a test that reads what a worker thread or the chooser has not done yet passes on this 24-processor machine and fails on the runner's four: ab5c214f, 4ebfabe8, ccee0eeb, 746095d2, 78870f1d, 903ca843, 9597265d, b9edeeb9, c83499f7, d11add5a, fcfdc92e, c5aaeaee, 5fc910eb, c148dfc6; also 70afdcfd and 41f77a6a (screen and pointer).
- **Before committing a new or changed test, run its file three more ways** (each a few seconds): (1) the floors venv: `env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -d -s "-screen 0 1280x1024x24" timeout -k 5 60 STATE/scratch/floorsenv/bin/python -m pytest test/<file>.py -q -p no:warnings -rs`; (2) Wine, for every new test, not only tests of paths (technique "The test suite under Wine"), and read "Windows: what the tests must not assume"; (3) a slow runner: the gate's command with `taskset -c 0-1` before `python3` and `-n 4`, five times over (`for i in 1 2 3 4 5; do ...; done`), which holds the eight-worker timing on two processors. No pytest-repeat is installed; loop in the shell.
- **The render-node trap**: never call `Gtk.Snapshot.to_node()` in a test without `try: ... except TypeError: self.skipTest(...)`; where the size or the paintable suffices, `snapshot.to_paintable(None)` is an ordinary GObject and runs under the floor too (5de90e7a). Reading pixels needs the node, so that test skips at the floor (e982e39f).
