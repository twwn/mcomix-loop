---
type: Technique
title: "Text that changes width: tabular figures and held widths in a label"
tags: [gtk]
sources:
  - { resource: "repo:mcomix/status.py" }
  - { resource: "repo:mcomix/theme.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-06T19:49:36Z" }
---

- (at 43a971a8) **The interface font's digits are proportional**: Adwaita Sans at 14.667 px sets "1111" at 24 px and "8888" at 37 (probe: a Gtk.Label per string in a window, read get_width() after a few turns of the loop). Pango.attr_font_features_new('tnum=1') in the label's AttrList makes them 39 each. GTK's own theme has no .numeric class (adding it changed nothing under plain Gtk); the attribute works under any theme.
- **tnum also spaces out hyphens and colons in this font**: "page-009.jpg" and "2024-05-06, 07:08:09" read as gappy. Give it to fields that are numbers only.
- **width_chars and set_size_request raise a label's minimum width too** (measured: an ellipsized label "12 / 120" min 13, nat 53; width_chars 12 gave min 108; size_request 150 gave min 150), which would hold the window wide. To raise only the natural width, subclass Gtk.Label and override do_measure: chain with Gtk.Label.do_measure(self, orientation, for_size) and return max(natural, held) for HORIZONTAL. status._Field does that; the room is measured with create_pango_layout(text) plus the label's own attributes.
- **A hidden label measures 0**: set it visible before reading measure() in a test.
- **Waiting for a label to be laid out**: wait_for until field.get_width() equals field.measure(HORIZONTAL, -1)[1] for each visible field (window wide enough that nothing is ellipsized). Gtk.Widget.should_layout() is "visible", not "needs layout": waiting on it gives up every time.
- **A Gtk.Window holding only a short bar is 200 px tall under Xvfb** and the bar is centred in it: a screenshot cropped to the top shows separators and no text. Put the bar in a vertical Box above a vexpand filler, as the main window does. The probe that took the before/after shots: STATE/probes/statusbar_shot.py (SHOT_OUT=<prefix>; MComixTest, theme.follow_theme(), import -window root -crop 1100x26+0+0), run with python3 -m pytest <file> --rootdir . from the checkout.
- **Under Wine, StatusbarHeightTest fails (heights {16, 17})** before and after 43a971a8; the Windows CI passed it at 90a9df97 (run 37491199283). Wine's fonts, not a bug.
- (corrected at bc9c4b5e) **A test that reads a render node skips below PyGObject 3.48**: 3.46, the floor, raises "No means to translate argument or return value for 'GskTextNode'" on Gtk.Snapshot.to_node(), and the CI's floors job failed on two such tests (run 37521842162). Use test_statusbar.drawn() or the guard in test_theme.py; check under SCRATCH/floorsenv (uv venv, PyGObject 3.46.0) before pushing a new one.
- (at 1ea5212f) **What colour a widget is drawn in, read from its render node**: `Gtk.WidgetPaintable(widget=w).snapshot(snapshot, w.get_width(), w.get_height())`, then `snapshot.to_node()`; a Gtk.Separator gives one Gsk.ColorNode (`get_color()`), a label's text node's `get_bounds()` gives where the ink stands (a little inside the text's logical width: 10.6 and 11.8 px either side of a centred "1 / 120"). Compare with `label.get_color()`, which is theme-independent. Adwaita's separator is alpha(currentColor, 0.15): rgba(0,0,6,0.12) light (text 0.8), rgba(255,255,255,0.15) dark and black.
- **Screenshots of each colour scheme in one process**: STATE/probes/statusbar_themes.py (SHOT_OUT=<prefix>, ALPHAS=0.5,0.35): sets prefs['colour scheme'] to light, dark, black in turn and calls theme.follow_theme(), draws a bar per scheme and strength, prints COLOURS lines, appends the crops into <prefix>-all.png. Put the scheme back to system at the end.
- **Narrow bars give way unevenly**: at 1100 px with every field and a double page, GTK's Box ellipsized the resolution and the file name while the path kept its full width (it shares out the room by how far each child is from its natural width). Not changed yet; see the notes' leads.
