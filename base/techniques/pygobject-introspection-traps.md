---
type: Technique
title: PyGObject introspection traps
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-25T03:04:01+02:00" }
---

- **`GObject.signal_list_names(<PyGObject class>)` answers `()` for every class**, `Gtk.Button` included, so it cannot show that a widget has no signals. Ask for one by name with `GObject.signal_lookup('file-activated', Gtk.FileChooserWidget)`, which answers 0 for a signal the type does not have; check the probe against a signal that certainly exists (`'clicked'` on `Gtk.Button`) first. It showed that GTK4's `Gtk.FileChooserWidget` keeps its keybinding signals (`location-popup`, `up-folder`, `show-hidden`) while a comment said it had none at all; what it lacks is `file-activated` and `update-preview`.
- **Two things PyGObject will not read back** (at b02c4901): a `Gdk.ContentProvider`'s value (`get_value()` raises "Invalid type" on PyGObject 3.5x and "unknown type (null)" on 3.46) - patch `Gdk.ContentProvider.new_for_value` with `wraps=` and assert the call; and `Gtk.DragSource` has `set_icon()` and no getter - hand the handler a stand-in with a recording `set_icon`.
- **PyGObject 3.46 names flag members after the typelib of the GTK it runs against**: Gdk.PaintableFlags has SIZE with GTK 4.14 and STATIC_SIZE with 4.22; 3.56 answers to both. Give a flag by value, `Gdk.PaintableFlags(1)`, where the stubs and the runtimes disagree.
