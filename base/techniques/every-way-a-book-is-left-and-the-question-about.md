---
type: Technique
title: "Every way a book is left, and the question about its changes"
tags: [code]
sources:
  - { resource: "repo:mcomix/file_handler.py" }
  - { resource: "repo:test/test_main_window.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-23T06:32:18+02:00" }
---

- The question about unwritten changes lives in `file_actions. before_closing()` and is reached from `file_handler.open_file()` and `close_file()` and `MainWindow.close_program()`.  Anything that calls `file_handler._close()` itself before one of those has already lost the answer: `_close()` clears `archive_type`, and `has_unsaved_changes()` then says there is nothing to ask about. `git grep -n "self._close()" mcomix/file_handler.py` lists them; at dbb76f04 the only one left is `_open_file()`'s own, after the answer.
- A path that changes state before opening (the folder walks move the file provider) runs whole inside `before_closing()` rather than relying on open_file()'s deferred open: `_once_dealt_with()`.
- Tests: `test_main_window.py` "turning past ..." set a change with `file_actions.swap_pages(1, 2)`, call `next_book()` or `previous_book()`, count `_save_prompts()`, then answer NO and wait for `get_path_to_base()` to change.
