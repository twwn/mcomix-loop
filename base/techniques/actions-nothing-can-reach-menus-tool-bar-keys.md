---
type: Technique
title: "Actions nothing can reach: menus, tool bar, keys"
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-23T22:32:16+02:00" }
---

- The actions are `window.actiongroup._by_name` (ui.ActionGroup); the menus and tool bar are the nested tuples `ui._MENUBAR`, `ui._POPUP` and `ui._TOOLBAR` (a tuple item is (submenu name, children), None a separator); key bindings are the keybinding manager's `_action_to_callback` / `_action_to_bindings`, whose names are a namespace of their own (scroll_*, execute_command_N, ...). A probe on MComixTest building a MainWindow and diffing the three sets ran in 0.55 s; at 26cc181f all 84 actions were reachable (invert_color by CTRL+I only).
- Preferences read into attributes: `grep -rn "self\.\w* = .*prefs\[" mcomix` lists them; each needs a refresh where the preference changes (update_space for the page gap).
