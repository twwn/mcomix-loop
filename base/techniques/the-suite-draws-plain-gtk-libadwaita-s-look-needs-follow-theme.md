---
type: Technique
title: "The suite draws plain GTK: libadwaita's look shows only after theme.follow_theme()"
tags: [gtk]
sources:
  - { resource: "repo:mcomix/theme.py" }
  - { resource: "repo:mcomix/run.py" }
  - { resource: "repo:test/__init__.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-11-17T18:40:00Z" }
---

- **Only run.py calls theme.follow_theme()**, which starts libadwaita where it is installed (it is here). No test does, so every test and every probe built on MComixTest draws with plain GTK's Default theme, and a styling bug that only libadwaita's stylesheet causes passes the suite. 3b75db50's floating shelf search field was white writing on an entry libadwaita draws as `alpha(currentColor, 0.1)`: unreadable for the user, opaque white in every test (fixed in 8b7b313f).
- **To see what the user sees**, a probe calls `theme.follow_theme()`, sets `prefs['colour scheme']` (system, light, dark, black) and `theme.apply_colour_scheme()`, then pumps. Adw.init() and its display-wide providers stay for the whole process, so this belongs in a probe, never in a suite test (another test in the same xdist worker would inherit it).
- **A suite test of such a bug** adds a stylesheet that does what libadwaita does, e.g. `entry { background-color: alpha(currentColor, 0.1); }` at STYLE_PROVIDER_PRIORITY_APPLICATION, removed with addCleanup(Gtk.StyleContext.remove_provider_for_display, ...).
- **Reading a widget's drawn colour without a screenshot**: `Gtk.WidgetPaintable(widget=w).snapshot(snapshot, width, height)`, then `window.get_renderer().render_texture(snapshot.to_node(), Graphene.Rect().init(0, 0, width, height))` and a `Gdk.TextureDownloader` set to R8G8B8A8: the widget alone, so the alpha byte says whether its ground is see-through (test_shelf.py test_the_field_is_drawn_solid_over_the_covers). (corrected at e982e39f) `to_node()` raises TypeError under PyGObject 3.46, the floors job's: wrap it and skip there ([A test that passes here and fails in the CI](a-test-that-passes-here-and-fails-in-the-ci.md)); on the Windows runner it returned None (lead 36).
- **Colour names both define**: libadwaita states `@define-color theme_base_color @view_bg_color` (and theme_text_color), and plain GTK's Default theme states theme_base_color too, so a rule naming @theme_base_color works under both. A rule naming @view_bg_color under plain GTK with the scheme "system" drew black (no definition): prefer the theme_* names where plain GTK must keep working.
- **This session's locale is German**: GTK's own labels in a probe's output come translated (`_Umbenennen`, not `_Rename`); match GTK's strings through `GLib.dgettext('gtk40', msgid)` or not at all.
