---
type: Technique
title: "Coverage: running it, and where it pays"
tags: [testing]
sources:
  - { resource: "repo:mcomix/scrolling.py" }
  - { resource: "repo:mcomix/archive/mobi.py" }
  - { resource: "repo:mcomix/file_chooser_library_dialog.py" }
  - { resource: "repo:mcomix/slideshow.py" }
  - { resource: "repo:mcomix/thumbbar.py" }
  - { resource: "repo:mcomix/preferences.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-26T15:13:41+02:00" }
---

- **pytest-cov 7.1 and coverage 7.15 are installed, and a covered run of the whole suite took 22-35 s under -n 8** when the suite was smaller; at 27 s uncovered (dc0c098f) give a covered run `timeout 120`. Keep the data file out of the repository:

  ```sh
  COVERAGE_FILE=<scratchpad>/.coverage env -u WAYLAND_DISPLAY GDK_BACKEND=x11 \
      timeout 60 xvfb-run -a python3 -m pytest test/ -q -n 8 -p no:cacheprovider \
      --cov=mcomix --cov-report=term-missing:skip-covered > <scratchpad>/cov.txt 2>&1
  grep -E "^mcomix/\S+\s+[0-9]+\s+[0-9]+\s+[0-9]+%" <scratchpad>/cov.txt |
      awk '{print $3, $4, $1}' | sort -rn
  ```

  **A coverage test written from what the code answers can write a bug down** (at 20c47bea): 4971e936 asserted that `get_home_directory()` is `~/MComix` on Windows because that is what it returned; it was the settings folder of before 2023, and HOME_DIR is where the choosers open. Before asserting an untested branch's answer, grep what uses it and ask whether the answer is right for them.

  The missed-lines column points at code no test runs, which is where a sweep for bugs pays best: scrolling.py at 26% was the space bar's whole algorithm.
- **Coverage is not the same from one run to the next** (at cbd3cb17): two covered runs of the same tree gave 746 and 742 lines missed, and image_tools 30 or 18 - the file_animates() fallback to glycin (560-562, 578-588) runs in some orders and not others. Compare coverage numbers across commits only as a range, or run twice.
- **The least-covered modules held three real bugs in one sweep**: mobi.py at 26% could not list a book at all (StopIteration from an extension-less gdk-pixbuf format, and Gio guessing nothing on Windows; 916d02f6), file_chooser_library_dialog.py at 32% crashed the process after its dialog closed (48150817), slideshow.py at 45% swapped the tool bar's icon for a smaller full-colour one (4300e3e3). Run the covered suite (section [Coverage](coverage-running-it-and-where-it-pays.md)), sort by percentage, and read the bottom five before anything else. A module no test imports at all is the best bet: the first test that merely opens the thing is often the one that fails.
- **At 3c867f60-239bc7cb the missed-lines column held two more**: the restore of expanded rows in collection_area.display_collections, whose elif skipped the selected row (8aaa4ec9), and the undo branch of file_actions._swap_names_on_disk, which ran its moves back first move first (239bc7cb). Error branches are the best part of the column: an undo is written once and never run. Drive one by patching `os.rename` with a stub that raises for the first call a predicate picks, and only the first: a stub that fails every matching call fails the undo's own rename too, and reports a bug that is not there.
- **Still true at 2be29947**: the first test written for thumbbar.py's uncovered drag handlers found that the sidebar's ThumbnailListView had no `model`, so get_item() - shared with the library's grid - raised on every drag from the sidebar. A method shared by two subclasses and exercised through only one of them is the place to look: read which attributes it needs and whether each subclass sets them. Handlers of real pointer input are reached in a test by calling them with a `unittest.mock.Mock()` for the controller or source; the real drag was checked once by hand with xdotool (SCRATCH test_zz_thumbdrag.py style: patch the class method before the window is built, since the controller holds the bound method).
- **Closing a coverage gap found a regression once** (2da60e21): the preference dialog mapped a pre-2012 integer "store recent file info" to Never/Always, but since 38376fdb the loader refuses a value of the wrong type, so the mapping was dead and a stored 0 became the default True. When a branch that reads an old form of a value is unreachable, ask what now happens to that old form on load. The sweep that followed compared every default of upstream's preferences.py (0128281) with the current `Preferences` annotations through `preferences._of_type`: no other mismatch.
- **Mutation driver.** `<scratchpad>/mutate.py`-style: a list of `(file, exact old text, new text, name)`, assert the old text occurs once, write, run one test file in a subprocess under xvfb-run, restore in a `finally`.  One process per mutation, about 0.5 s each for a small file. `git status --short` afterwards proves every file came back.
