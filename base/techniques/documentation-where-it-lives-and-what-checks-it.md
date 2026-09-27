---
type: Technique
title: "Documentation: where it lives and what checks it"
tags: [text]
sources:
  - { resource: "repo:pyproject.toml" }
  - { resource: "repo:test/test_wiki.py" }
  - { resource: "repo:docs/README.md" }
  - { resource: "repo:test/test_keybindings.py" }
  - { resource: "repo:test/test_openwith_command.py" }
  - { resource: "repo:mcomix/preferences_dialog.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-26T15:10:37+02:00" }
verified:
  - { by: claude.ai/claude-opus-5.5, at: "2026-09-28T16:40:18Z" }
---

- **The manual is `docs/*.md` in GitHub Markdown** since ec577bb5, with the screenshots in `docs/images/` and an index in `docs/README.md`. The repository's own `README.md` is its front page: what MComix is, and what this fork adds on top of upstream 3.2.  There is no wiki, no Allura markup and no sync tool any more, so a page is edited in place and nothing has to be pushed anywhere.
- **`test/test_wiki.py` is the accuracy gate.**  It compares `docs/preferences.md` with every label and tab `preferences_dialog.py` builds (and with the obsolete messages in the catalogues, so an option the program dropped cannot stay on the page), `docs/reading.md`, `editing.md` and `library.md`, read as one, with the defaults and the menu labels they quote, `docs/install.md` and its dependency floors with `pyproject.toml`, `docs/development.md` and `docs/releasing.md` with the files and paths their recipes name, and `docs/images/` with the images the pages show (page names as of 9ea3d7fe). `test/test_keybindings.py` does the same for `docs/shortcuts.md`, and `test/test_openwith_command.py` for the variables on `docs/external-commands.md`.  A page renamed or moved has to be repointed in all three.
- **Rendering a page** is `cmark-gfm -e table <page> > /dev/null`, and the relative links are checked by walking `](target)` for every page and asking whether the path exists next to it; both found nothing after the move, which is what makes them worth re-running after one.
- **Links that name the project** all point at <https://github.com/twwn/mcomix>: `pyproject.toml`'s URLs, the about dialog's website, the external-commands dialog's help link, the AppStream homepage and update contact, the Chocolatey metadata and the MSI the package downloads, and the `--msgid-bugs-address` in the translation recipe (so the catalogues' headers carry it too).  What stays `net.sourceforge.mcomix` is the AppStream component id, the developer id and the Flatpak application id: they identify the installed application, and renaming one installs a second application beside the first.
- **A substring of the module's source is not a label.** `test_wiki.py` checked quoted dialog labels with `label in source.replace('_', '')`, and renaming the "Automatically adjust contrast" check box still passed: its tooltip repeats the words.  Compare with the module's translated strings instead - `translated()` over `ast.walk(parse_module(module))`, underscores removed, a trailing colon or ellipsis stripped - and prove it by renaming the `_('...')` argument alone.  Short labels ("OK", "Save") cannot be looked for on a page at all: they occur inside other words.
- **Links between the pages (9ea3d7fe): `test_wiki.LinksTest`.** It follows every relative Markdown link in docs/, README, CONTRIBUTING, SECURITY, ChangeLog and the PR template to a file and, for a `#fragment`, to a heading; and every `github.com/twwn/mcomix/blob/main/` or raw link in mcomix/**/*.py, pyproject, the nuspec, share/ (the man page gunzipped) and the workflows.  Anchors are made as GitHub makes them: lowercase, drop all but `\w`, `-` and space, spaces to hyphens, duplicates `-1`, `-2`; fenced code skipped.  GitHub does not redirect a renamed file, and a released MComix keeps its dialog's link for good.
- **A relative link in a PR or issue template is broken**: it resolves against the pull request's URL, not the repository.  Use absolute `https://github.com/twwn/mcomix/blob/main/...` links there.
- **Checking a rewrite kept every quoted label**: collect `re.findall(r'"([^"\n]{2,60})"', old)` plus backticked spans from `git show HEAD:<old page>` and look each up in the new pages joined; wider patterns pair quotes across prose and list noise.
- **Claims a page makes that the code decides**, checked before writing them (9ea3d7fe): opening an image lists its folder (`file_provider.OrderedFileProvider`); drops on the page open files (`event.py`, `Gtk.DropTarget`); smart scroll turns the page at the end (`event._smart_scrolling`); About is in the File menu (`ui._MENUBAR`); `--version` prints nothing from the windowed MComix.exe (argparse writes to a None stdout and swallows the AttributeError); the MSI installs to `C:\Program Files\MComix` (`ProgramFiles64Folder`).
