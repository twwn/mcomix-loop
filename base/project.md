---
type: Installation
title: This installation
generated: { by: claude.ai/claude-opus-5.5, at: "2026-09-27T12:00:00Z" }
---

# This installation

Copy to `state/project.md` and replace every fact below with yours. The loop reads it at the end of its prompt and never edits it; when the tree contradicts it, the loop records that under `Prompt corrections` in its notes for you to fold in. Rulings given in conversation are in `decisions/`, one file each, which the loop writes and you confirm; this file is what you keep. This example is the author's installation as of 27 September 2026.

A hash here is a pointer, not an identity: the loop never rewrites history, but I have, by hand, more than once, and a hash that no longer resolves means the commit was rewritten, not that the fact is wrong — find it by its subject.

## Where the code stands

- The repository is <https://github.com/twwn/mcomix> (`origin`, `git@github.com:twwn/mcomix.git`), branch `main`; this loop is <https://github.com/twwn/mcomix-loop>. The history is curated on 0128281, upstream's last GTK 3 tree; `archive/*` tags keep the pre-curation originals. **Pushing is mine, by hand**; the guard refuses `git push` and everything in `gh` but reading.
- **CI**: GitHub Actions on a push: `tests.yml` (the `gates` jobs across Python versions, and `floors`, the dependency floors), `windows-tests.yml` (the suite under MSYS2 UCRT64 on Windows), `codeql.yml`; `release.yml` and `publish.yml` on a pushed tag. The technique "The GitHub CI: reading its results, reproducing its jobs" has how to read them with `gh` and how to reproduce each job here.
- **Versions are CalVer**, `YY.MM`; a second release in the same month is `YY.MM.1` (`docs/releasing.md` states it). `mcomix/constants.py` carries no `-dev0` between releases. The first GitHub release is 26.09; its notes link to the ChangeLog's 4.0.1 and 4.0.0 sections.
- **A release is a commit I order**, and that commit writes `VERSION`, the `ChangeLog.md` section with its date, and the AppStream metainfo `<release>` entry. No `(unreleased)` section is opened beforehand and no ChangeLog line is written meanwhile: the release commit gathers them from `git log`. The tag is mine; pushing it runs the release workflow, which builds the Windows packages and publishes the GitHub release with the three built files (8290f9a3), and its publish job submits the Chocolatey and winget packages where their secrets are set. `docs/releasing.md` has the procedure.
- The manual is `docs/*.md` in the tree, one page per task, screenshots in `docs/images/`, `README.md` the front page. There is no wiki. `docs/install.md` describes this fork's packages, not upstream's. What stays `net.sourceforge.mcomix` on purpose is the AppStream component id, the developer id and the Flatpak application id: they identify the installed application, and renaming one installs a second beside the first. Historical ChangeLog entries and the links to Comix keep their names.
- The Chocolatey package is this repository's, published from the `twwn` account under the id **`mcomix-gtk`** — an id that names neither the owner nor a version, so neither `mcomix-twwn` nor `mcomix4`.
- This machine runs Arch with Python 3.14 and GTK 4.22 (glycin installed); the shell the Bash tool runs is zsh. `/tmp` is a tmpfs.

## Finished campaigns

Do not reopen without asking.

1. **Deprecations.** Sixteen names are reached, all accounted for, and none can go: eleven `Gtk.FileChooser.*`, because `Gtk.FileDialog` is modal-only and MComix embeds a chooser, and the `wip/file-browser` branch that replaces it stays out; four `GdkPixbuf.PixbufAnimation*`, the last-resort decoder for a tree without glycin (the Windows build of GTK) and a file Pillow will not open, which GTK deprecated with nothing in its place; one that PyGObject raises about its own API (`GLib.unix_signal_add_full`). Two more, asyncio's from `gi.events`, are filtered in `test/pytest.ini` since 754140ea.
2. **Typing.** mypy runs at `--strict` plus `disallow_any_explicit` and reports nothing.
3. **Dialogs freed on close** (aa498a4f): every dialog lets go of itself when it closes; `test/test_dialog_freed.py` holds it there.
