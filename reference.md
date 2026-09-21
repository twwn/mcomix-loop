# MComix loop: reference

Rules and facts about the MComix GTK4 code base that hold for many
iterations, split out of `SKILL.md` so that the protocol comes first when the
harness truncates the skill after a compaction. Facts about one installation
— fork, review status, decisions, finished campaigns — are in
`state/project.md`. Do not edit either; record contradictions under `Prompt
corrections`.

## The task list

- **Bugs** of every kind: logic, uncaught cases, races, state that outlives
  what owns it.
- **Speed**, measured, on the paths that run per page turn first.
- **Idiom and structure**, with the standards in `SKILL.md` for refactors.
- **Comments** that describe the code as it is now. Delete the ones that
  narrate a fixed bug or a removed workaround; write the missing ones where
  the code is genuinely not obvious; complete a comment that has drifted.
- **Workarounds and deprecations.** Remove shims for versions the floors no
  longer allow, and say which version made each unnecessary. List what the
  suite still reaches with `gates.sh deprecations`. A deprecation notice
  names a replacement; check the replacement can do the job before porting
  to it. The names still reached are listed with their reasons under "Finished
  campaigns" in `state/project.md`; a new name there is a regression unless a
  new test is what reached it (compare with `--ignore=<that test file>`).
- **Incomplete features**: options defined but never read, actions with no
  way to reach them, a behaviour offered in one place and missing from its
  twin.
- **SQL** in `mcomix/library/backend.py` and its callers: a `WHERE` no index
  covers (a composite primary key does not serve its second column), per-row
  loops where one statement would do, bulk writes outside
  `backend.transaction()` — the connection auto-commits every statement.
- **Dependencies**: prefer what the raised floors now permit. Raising a floor
  is the user's decision; ask under `Questions for the user`.
- **Translations**: complete and correct.
- **Typing**: keep mypy at zero, and read what is already annotated for types
  that are accepted but say nothing.

The standing emphasis, when no bug is known, is optimization, idiomatization
and refactoring, with documentation and comment coverage close behind.

## Project facts

- **A release date is the maintainer's**, written by the release commit
  (`docs/Maintenance.md` has the procedure). Nothing before that carries a
  guessed one: `ChangeLog.md` heads the open section `<version>
  (unreleased)` and the AppStream metainfo's `<releases>` gets its entry in
  the release commit. A plausible date is worse than a missing one, because
  nothing can tell it from a right one afterwards.
- **Python floor 3.12.** The machine running the loop is usually newer, so a
  feature past 3.12 works here and breaks a supported install. Review
  <https://docs.python.org/3/deprecations/index.html> at that baseline when
  touching anything it lists.
- **Dependencies:** the floors in `pyproject.toml` are the truth; optional
  chardet and PyMuPDF, the latter at the version `PYMUPDF_VERSION_REQUIRED`
  in `mcomix/archive/pdf_multi.py` names, which a test enforces. Numbers
  are not repeated here because they drift. `pygobject-stubs` is built for GTK4 by default, which is what
  this code uses.
- **Archive handlers** in `mcomix/archive/`: zip, tar, rar (libunrar and
  external), 7z, lha, PDF (native PyMuPDF and external mutool), mobi.
- **Translations:** `mcomix/messages/mcomix.pot` and one catalogue per
  language, `.po` and compiled `.mo` both committed. GTK's own catalogues
  (`/usr/share/locale/<lang>/LC_MESSAGES/gtk40.mo`) are LGPL and a legitimate
  source for common button labels.
- **The hot path** is `image_tools.load_pixbuf` and everything reached from
  `MainWindow.set_page`. Where gdk-pixbuf's loaders are sandboxed by glycin,
  any gdk-pixbuf call that touches a file costs about as much as decoding it,
  so a Pillow header read is far cheaper.
- **Structure:** `MainWindow` in `mcomix/main.py` draws, lays out and
  navigates; the operations on the book's files and their undo stack are
  `FileActions` in `mcomix/file_actions.py`.
- **Test data** is in `test/files/`: images in several JPEG and PNG modes
  with Exif-rotated variants (described in `test/test_image_tools.py`), and
  68 archives including encrypted ones (password `password`).
- `flake8` ignores E501 by configuration; `--select=F` is the gate.
