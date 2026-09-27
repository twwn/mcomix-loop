---
type: Technique
title: "GTK's own documentation, offline"
tags: [gtk]
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

`/usr/share/gir-1.0/Gtk-4.0.gir` carries every doc string GTK's introspection data was built from, and answers what a property or method actually promises when PyGObject's `find_property(...).get_blurb()` returns None (it does for most of GTK 4.22). Properties appear once per class, so find the class first:

    awk -v L=<line> 'NR<=L && /<class name=/ {c=$0} NR==L {print c; exit}' \
        /usr/share/gir-1.0/Gtk-4.0.gir

after `grep -n 'name="single-click-activate"'` has given the lines. The `filename=` attribute on each `<doc>` names the C file it came from, which tells ListView's copy from GridView's and ColumnView's.
