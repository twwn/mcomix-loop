## Gate numbers as of e833b8e6 (seed from another installation; re-baseline)

    pytest -n 8     3104 passed, 12 xfailed (776 subtests), 19-22 s
    flake8 -F       silent
    mypy mcomix     no issues in 161 source files
    catalogues      24 of them, 664 translated messages each, none fuzzy

Quiet iterations: 0

## Campaign

None open.

## Decisions from the user

None here; the standing ones are in STATE/project.md.

## Questions for the user

None.

## What the last iteration changed

Nothing on this installation yet. These notes were seeded from another
installation; the gate numbers above are that checkout's, and the leads
below were true there. Re-baseline the gates on a clean tree, then rewrite
this file as your own.

## Leads worth picking up

1. Not yet swept: the library's own dialogs against the book-close
   question (LOOP_TECHNIQUES "What follows a book that moves or goes").
2. What the suite's 25,000-odd Python warnings are: the 18 deprecation
   names are all accounted for (see project.md), so the rest are something
   else. `grep -oE '[A-Za-z]+Warning' SCRATCH/pytest.txt | sort | uniq -c`
   is the first cut (LOOP_TECHNIQUES "The suite's own warnings are a sweep").
3. Low coverage still unread: process.py 63% (130-201), portability.py
   65%, collection_area.py 66%, event.py 69%, openwith.py 71%, as of an
   earlier sweep that found 3 bugs; the command is in LOOP_TECHNIQUES
   "Coverage".

## Checked and rejected

- ac8209e2's claim re-checked: `git show --stat ac8209e2 | grep -c "\.mo"`
  still prints 0.
- 207c3715's subject says "all 25 catalogues"; there are 24
  (`ls mcomix/messages/*/LC_MESSAGES/mcomix.po | wc -l`). Not rewritten;
  this is the record.
- Everything the note at ac8209e2 listed still stands (the
  `gtk_root_get_focus` assertion, preference tooltips, the editor's double
  fetch, the slideshow's `_stop()`, subscriptions outliving their window,
  3.12 idiom, `except Exception`, text used as a pattern, the port sweeps);
  `git show ac8209e2` reaches it through the notes' history.

## Prompt corrections

None.
