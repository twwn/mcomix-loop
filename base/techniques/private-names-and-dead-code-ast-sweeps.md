---
type: Technique
title: "Private names and dead code: AST sweeps"
tags: [testing]
sources:
  - { resource: "repo:mcomix/main.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-24T07:38:42+02:00" }
---

- (at de191da4) `ast.walk` over every file under mcomix/, keeping each `Attribute` whose `attr` starts with one underscore and whose value is not `self`, `cls` or `super()`, lists every reach into another object's or module's private name with its first file:line.  Grep cannot do it: git grep colours its output, so `grep -v self` on it filters nothing. What it found at 46f4d43c and was fixed: a stdlib private function (`gettext._expand_lang`), a private helper called from two modules, two private attributes written from outside, one private module global read from two modules.  What is left is module-private classes (`backend_types._Book` and the like) used by their sibling modules: a naming convention, not a defect.
- **Functions nothing calls: STATE/probes/dead_defs.py** (at 88719431) counts identifier tokens over every tracked .py file and prints each def under mcomix/ whose name occurs only once. At a042d69d it listed ten; one was a false positive (bookmark_menu builds `'_%s_activated' % name` for getattr), so check non-literal getattr() calls before removing anything. Follow each removal one step: a getter removed can leave the attribute it read written and never read (file_chooser_simple_dialog._paths, a463e922), and a method removed can be the only reader of a whole mechanism (the canvas' motion controller fed only get_layout_pointer_position). Left at 88719431: clear_selection (a question for the user) and book_area.remove_book_at_path; the first got a menu entry and Escape (7abcbc54), the second went (26b5e699).
- **Attributes set and never read: STATE/probes/write_only_attrs.py** (at 24b4b352) lists every self.<name> stored under mcomix/ with no load of .<name> on any object and no string naming it anywhere in the tree. It errs towards silence (a load of the same name elsewhere counts); at d002c0e0 it listed six, all dead.
- (at 848a858e) The AST sweep is saved as STATE/probes/private_reach.py (run from the checkout's root; name, count, first file:line).  It listed 56 names; the one fix was edit_dialog._close_dialog(), called from main.py.  Re-running the [Sweeps that found work](sweeps-that-found-work.md) at 848a858e found nothing else: `except Exception` 36 handlers (38 at ba358e90), the text-mode `open()` without an encoding down to the three JSON reads, and `gates.sh deprecations` the 18 accounted names.
