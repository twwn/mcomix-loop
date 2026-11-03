---
type: Technique
title: "A Wayland compositor for a probe: headless sway, grim, and test/__init__ pinning X11"
tags: [gtk]
sources:
  - { resource: "repo:test/__init__.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-05T15:10:00Z" }
---

- **The reader runs sway** (`XDG_CURRENT_DESKTOP=sway`, sway 1.12), so a report of a window drawn wrong can be checked under the same compositor, headless, without touching the real session.
- **Run it:** a config file with `xwayland disable`, `output HEADLESS-1 resolution 1920x1080` and `exec sh -c 'cd <checkout>; GDK_BACKEND=wayland python3 <probe> > <log> 2>&1; swaymsg exit'`; then `env -u DISPLAY -u WAYLAND_DISPLAY -u SWAYSOCK XDG_RUNTIME_DIR=<scratch dir, mode 700> WLR_BACKENDS=headless WLR_LIBINPUT_NO_DEVICES=1 WLR_RENDERER=pixman timeout -k 5 60 sway -c <config>`. sway exports WAYLAND_DISPLAY and SWAYSOCK to what it execs.
- **`xwayland disable` is required:** with Xwayland on, sway sets DISPLAY, and test/__init__.py then pins GDK_BACKEND=x11 and drops WAYLAND_DISPLAY (to keep the suite off the reader's desktop), so the probe silently runs on X.
- **Seeing it:** `grim <png>` from inside the probe takes the output; `swaymsg -t get_tree -r` gives each window's rect, a dialog as a `floating_con` with its `window_rect` (the size the client chose).
- At 273f3fe3 the trash-refused offer came out 389x145 floating, both buttons drawn, the same as under Xvfb; the probe was STATE/scratch/probe_edit_delete.py (edit, Apply, Save As, Delete), built on MainWindowTest and run as `Probe.test_flow` (the class name alone runs all 224 inherited tests).
