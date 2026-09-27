---
type: Technique
title: "Library writes from the UI: two statements a book is seconds on disk"
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-23T21:08:07+02:00" }
---

- **Auto-commit costs about 4 ms a statement on this machine's xfs** (300 books x insert+delete: 2.414 s auto-commit, 0.015 s in one BEGIN IMMEDIATE ... COMMIT). /tmp is tmpfs, so a benchmark run under MComixTest's temporary home hides it: run the raw statements with `sqlite3.connect(<SCRATCH>/bench.db, isolation_level=None)`.
- **A test proves the transaction by tracing, not timing**: `backend._con.set_trace_callback(statements.append)` shows the sqlite3 module's own `BEGIN IMMEDIATE` and `COMMIT` once the connection's isolation level is set; under auto-commit it shows neither. Require one BEGIN before the first write and one COMMIT after the last (test_collection_area `test_books_moved_are_written_in_one_transaction`).
- Loops checked at 9a7bf625: add_progress_dialog, book_area's two removes, last_read_page's clear are wrapped; the drop handler now is; last_read_page's migration of the old lastread database is not, and runs once from an upgrade step.
