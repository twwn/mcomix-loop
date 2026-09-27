---
type: Technique
title: What follows a book that moves or goes
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-20T07:02:24+02:00" }
---

- MComix records a book's path in five places, and each one has to be brought forward when "Move to" moves the file (see `FileActions.move_current_file`):
  - the library, `backend.LibraryBackend().update_book_path()`;
  - the store of last read pages, whose old entry is cleared;
  - the bookmarks, `BookmarksStore.update_path()` (3a7612d7);
  - the recent files, whose old entry is removed while reopening the book records the new one (917cf8fe);
  - the "moved to before" destinations, which hold the folder rather than the book and need nothing. Deleting the file instead forgets the path in the recent files (42ed9bbc) and clears the last read page; the bookmarks and the library entry are left standing, because removing a reader's bookmark is not something a delete should do quietly.
- The pattern to check when anything new records a path: grep for the five, and ask which of them the new code has to tell.
