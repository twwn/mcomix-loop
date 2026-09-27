---
type: Technique
title: Threads that share one thing
tags: [gtk]
sources:
  - { resource: "repo:test/test_image_handler.py" }
  - { resource: "repo:test/test_library_dialog.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- **One sqlite3 connection shared by threads fails without a lock, even with `sqlite3.threadsafety == 3`.**  sqlite3 caches prepared statements per connection, and two threads running the same text at once step the same statement.  A bare probe of four threads making two point lookups a round for two seconds got 13,177 errors in 87,726 rounds ("bad parameter or other API misuse", "another row available", and silent None answers).  `cached_statements=0` stops it at 50-85% more per statement; a lock held from execute to cursor close stops it at 4-11% (e36960a9).  The backend's execute(), fetchone() and fetchall() hold that lock; a new statement must go through them, never through `_con`, and a listener must never be called while the lock is held (the lock is not reentrant).
- **Make a race deterministic by parking the worker inside the slow call.**  Patch the module attribute the code calls at run time (`image_tools.load_pixbuf`) with a function that sets one Event and waits on another; start the thread, wait for the first Event, do the main-thread action, set the second, join.  The 00a test in test_image_handler.py is the model.
- **Stand in for an archive handler by wrapping the real one** after the extractor has listed it: an object whose `__getattr__` delegates and which overrides `is_solid()` and `iter_extract()`.  `close()` still reaches the real archive through the delegation.
- **A real solid pass that fails:** `os.chmod(destination, 0o555)` before `extract()` makes the 7z handler raise PermissionError on its first file.  Restore the mode before the temporary directory is removed.
- **Library covers in a real window:** `_LibraryWindowTest` from test_library_dialog.py, `dialog.backend.add_book()` for a handful of test archives, `prefs['library cover size'] = 50` (below 50 the cover worker never asks for the page read), then `book_area.display_covers(None)` and count `item.thumbnail is not None` over `book_area._each_item()`. Patch `mcomix.log.error` to collect what the worker threads log.
