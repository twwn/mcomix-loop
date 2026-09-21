# This installation

Copy to `state/project.md` and replace every fact below with yours. The loop
reads it at the end of its prompt and never edits it; when the tree
contradicts it, the loop records that under `Prompt corrections` in its notes
for you to fold in. This example is the author's installation as of
21 September 2026.

## Where the code stands

- The repository is <https://github.com/twwn/mcomix>, this loop is
  <https://github.com/twwn/mcomix-loop>. Master is the curated history on
  0128281; `archive/*` tags keep the pre-curation originals. A pull request
  of the GTK4 port to the upstream maintainer is open; master is never
  rewritten, and what is pushed is my decision, not the loop's.
- Releases are GitHub releases with the three built files attached;
  `docs/Maintenance.md` has the procedure, and the release commit is what
  writes the ChangeLog date and the metainfo `<release>` entry. The current
  version is what `mcomix/constants.py` says.
- The manual is `docs/*.md` in the tree, screenshots in `docs/images/`,
  `README.md` the front page. There is no wiki. What stays
  `net.sourceforge.mcomix` on purpose is the AppStream component id, the
  developer id and the Flatpak application id: they identify the installed
  application, and renaming one installs a second beside the first.
  Historical ChangeLog entries and the links to Comix keep their names.
- A schema change while the pull request is open is a question for me, under
  `Questions for the user`, not a commit: the `_LibraryBackend.DB_VERSION`
  step on the branch is published, so extending it changes what is under
  review and adding a step commits the release to two migrations.

## Standing decisions

Each holds; the hashes are where the loop can read the reasoning.

- I install MComix by hand from the checkout, so a fix is not in the
  installed program until I reinstall.
- Commits carry no `Co-Authored-By` or other trailer.
- `wip/file-browser` stays out of the release.
- Changing the interface language offers to restart MComix rather than
  reloading the interface in place.
- A format that needs an outside program is offered only where that program
  is installed; nothing may assume 7z or rar is present.
- What a delete takes with it: 5ee79c84, 59f23a30. The swap gesture and its
  mark: f28db1de, ec97e760, 10fac538. How renaming behaves: 6d7911ba,
  a986339e, 48793054, 3d852d50, be264545. The unwritten-change questions,
  and that the editor's may keep the book open: 86be9e64, 2e91651f,
  add07972. No batch rename: 38fa1a0e.

## Finished campaigns

Do not reopen without asking.

1. **Deprecations.** Eighteen names remain, all accounted for, and none
   can go on master: eleven `Gtk.FileChooser.*`, because `Gtk.FileDialog`
   is modal-only and MComix embeds a chooser, and the `wip/file-browser`
   branch that replaces it stays out; four `GdkPixbuf.PixbufAnimation*`,
   the last-resort decoder for a tree without glycin (the Windows build of
   GTK) and a file Pillow will not open, which GTK deprecated with nothing
   in its place; three that PyGObject raises about its own API and no
   MComix code calls.
2. **Typing.** mypy runs at `--strict` plus `disallow_any_explicit` and
   reports nothing.
