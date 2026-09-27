---
type: Technique
title: "The library window in a test: covers, drops and scans"
tags: [code]
sources:
  - { resource: "repo:test/test_library_dialog.py" }
  - { resource: "repo:test/test_book_area.py" }
  - { resource: "repo:test/test_main_window.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-23T17:38:52+02:00" }
---

- **`test_library_dialog.py:_OneBookTest` is the real library with one book shown under "All books"**; subclass it rather than the stubs in test_book_area.py when what is tested crosses the book area, the control area and the backend. `_left_on(page)` writes the recent row (last page = finished). Select a cover with `book_area._covers.select_only(0)` and pump; the info line is `control_area._namelabel/_filelabel/_dirlabel`.
- **The covers are drawn by worker threads, and a worker can still be drawing the cover `display_covers()` asked for when the test changes the book.** A test that counts what drawing a cover does, or reads something drawing caches, calls `book_area.stop_update()` in `setUp` and then draws with `book_area._get_pixbuf(uid)` on the main thread. 1f8e522b stopped the worker after marking the book finished, and the worker made the cached mark first (count 0 instead of 1).
- **A drop from a file manager is `book_area._drag_data_received(None, files, 0, 0)`** with `files = types.SimpleNamespace(get_files=lambda: [Gio.File.new_for_path(path)])`; a scan's result is `dialog._new_files_found([path], SimpleNamespace(collection=..., directory=...))`. Wait with `wait_for(lambda: backend.get_book_by_path(path) is not None)`: the progress dialog adds the books inside the main loop.
- **Read `Contain` directly** (`backend.fetchall('select collection, book from Contain')`) to see where a book was filed: the typed getters join Collection and hide rows for ids that have no row, such as -1.
- **`_LibraryDialog.add_books(paths, collection_id)`** since 6d4958ae: None, COLLECTION_ALL and COLLECTION_RECENT all file in no collection. A new book filed nowhere raises only `backend.book_added`, which the cover grid now listens to as well as `book_added_to_collection`.
- **`prefs['last library collection']` is also what `_collection_selected()` compares with**, so setting it without showing that collection makes picking it in the sidebar do nothing. Only the code that changes what is shown should write it.
- **To catch the covers mid-drawing, hold the worker on an event, not a sleep, and only briefly** (test_library_dialog.py OpenFromLibraryTest): wrap `book_area._covers.generate_thumbnail` in a function that waits on a `threading.Event` for at most a second. Anything that redraws the covers (`set_items`, `clear`, a book opened and written to "Recent") calls `stop_update()`, which joins the worker, so a long hold becomes a stall of the main thread: at 5 s the test passed but took 5 s, one run in six under -n 8.
- **Adding every archive in test/files/archives to the library hangs**: the encrypted ones ask for a password on the main thread. Filter out names containing "ncrypt" or "assword".
- **A "Save and quit" resume is tested by two windows in one test** (test_main_window.py ResumeAfterSaveAndQuitTest): set the preference, `window.write_config_files()`, close the window, and build a second `MainWindow()` with no path.
