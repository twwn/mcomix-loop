---
type: Technique
title: "Text a reader typed, used as a pattern"
tags: [code]
sources:
  - { resource: "repo:test/test_library_types.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-20T06:43:40+02:00" }
---

- Every place a preference or a filter box reaches a matcher is a place where the text is read as a pattern unless something stops it. Find them with `grep -rn "LIKE\|re.compile(\|fnmatch\|glob" mcomix/` and ask of each where the string comes from. At 062b73d9 there were four:
  - the library's filter, which went into SQL `LIKE` unescaped, so "%" listed the whole library (fixed in 561d10a6 with `_contains()` in library/backend_types.py, which quotes `%`, `_` and the quoting character, and `ESCAPE '\'` on each LIKE - SQLite has no default escape character, so the clause is needed);
  - the "comment extensions" preference, joined with `|` into a regular expression, where "c++" matched "cc" and a lone "(" raised re.error inside FileHandler's constructor and stopped MComix starting (fixed in 062b73d9 with `tools.fixed_strings_regex()`, which escapes and sorts, and is what the format patterns already used);
  - the names handed to external unzip, which reads a member name as a shell pattern - archive/zip_external.py wraps `[`, `*` and `?` and doubles a backslash, and says so;
  - the file chooser's `fnmatch` filters, whose patterns MComix builds from the formats it supports, not from anything typed.
- A LIKE with a leading wildcard is served by no index either way, so escaping changes no query plan; test_library_types.py asserts the plans and passed unchanged.
