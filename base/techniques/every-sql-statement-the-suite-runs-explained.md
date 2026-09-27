---
type: Technique
title: "Every SQL statement the suite runs, explained"
tags: [code]
sources:
  - { resource: "repo:mcomix/library/backend.py" }
  - { resource: "repo:mcomix/library/backend_types.py" }
  - { resource: "repo:mcomix/last_read_page.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-22T23:15:01+02:00" }
---

- (at 4bd8e7e2) STATE/probes/sqltrace_plugin.py wraps `sqlite3.connect` so every connection records its statements (expanded, with values) to `$SQLTRACE_DIR/<pid>.sql`; run the suite with `PYTHONPATH=STATE/probes SQLTRACE_DIR=<dir> ... pytest test/ -n 8 -p sqltrace_plugin` (make the directory with `rm -rf; mkdir`: zsh aborts a `&&` chain on an `rm` glob that matches nothing). STATE/probes/sql_plans.py <dir> rebuilds the schema in memory from the traced CREATE statements, folds literals so one statement counts once, and prints every statement whose plan scans a table, with how often the suite ran it.
- (at 848a858e) 22,734 statements, 101 distinct, 28 that scan (the same set as at 4bd8e7e2) - none a defect: they scan collection, watchlist, recent or lastread (small, or read once at a migration), or list the whole library on purpose ("All books", the scan's list of known paths, the filter's LIKE). Rerun after any change to backend.py, backend_types.py or last_read_page.py.  The book-table scans are the whole-library listings above, migration step 8's `where book not in (select id from book)`, and test_library_backend's own queries.
