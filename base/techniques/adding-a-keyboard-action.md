---
type: Technique
title: Adding a keyboard action
tags: [code]
sources:
  - { resource: "repo:mcomix/event.py" }
  - { resource: "repo:mcomix/keybindings.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-20T06:51:40+02:00" }
---

- A key that does something new is registered as an action, never read out of a key handler: the reader can then rebind or clear it in the Shortcuts tab, and the loop's own sweep ("the keybinding table and event.py's registrations match exactly") stays true. Four places, all in one commit (798eb5e0 is the worked example):
  - `keybindings.py` `BINDING_INFO`: `'name': {'title': _('...'), 'group': _('...')}` - the title is a new translatable string;
  - `event.py` `_register_keybindings()`: `manager.register('name', ['Menu', '<Shift>F10'], <callable>)`, where each default is a string `Gtk.accelerator_parse()` understands (check it: it answers `(True, keyval, mods)`);
  - `docs/shortcuts.md`, in the table the function belongs to;
  - the catalogues, as any new string.
- A handler that a key reaches has no pointer position to work from, so anything that reads one needs an answer of its own: the page menu's `popup_page` becomes the page on screen rather than the page under the pointer, and `widgets.popup_at()` is given the middle of the page area.
