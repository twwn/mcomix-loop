# Techniques that paid off on MComix

Nothing here is ever deleted; a wrong statement is corrected in place. This
file is what LOOP_NOTES used to carry in its last section, moved out because
the notes are capped at about 80 lines and rewritten every iteration, so
anything durable competed with the leads for room and eventually got
dropped. Nothing here is iteration state; it is what is true about measuring
and testing this code base. A probe or script named here as
`STATE/probes/<name>` is kept there, beside this file, so that the technique
and its instrument travel together.

## Running things

- **Always under Xvfb**, and with X rather than Wayland:
  `env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -a ...`. A bare pytest
  run against no display hangs rather than failing.
- **`-n WORKERS` (`STATE/config.sh`; 8 on a 24-core machine) is the measured
  optimum** for the suite, about nine seconds against thirty-three serial.
  `-n auto` fans out to every core and is slower: worker startup dominates a
  suite this short. `--dist loadfile` is the fallback if shared state starts biting.
- **Timeouts belong on every run.** 60s is plenty for the suite and any
  probe, 120s for mypy. A longer timeout hides a hang instead of surfacing
  one — which is how the `_BookArea` hang below was found.

## Probes

- **`MComixTest` is the base class for any ad-hoc script.**
  `mcomix/constants.py` resolves `CONFIG_DIR`, `DATA_DIR` and about ten
  derived paths **at import time**, so setting `HOME` and the `XDG_*`
  variables is not enough; the constants have to be reassigned, and
  `test/__init__.py` already does it correctly. Getting this wrong has
  destroyed a preferences file and leaked test files into the reader's
  recently-used list. Run one with
  `unittest.main(argv=[sys.argv[0], 'Probe'])` and then `os._exit(0)`:
  leaving the GTK main loop does not end the process, because MComix'
  worker threads are not daemons, and `os._exit` does not flush, so flush
  stdout first.
- **`Gtk.RecentManager.get_default()` writes to
  `~/.local/share/recently-used.xbel`.** Patch `get_default` to return a
  `Gtk.RecentManager(filename=<temp>)`.
- **A GUI probe must destroy its windows.** A dialog left on screen is
  answered by the next test that goes looking for one, which shows up only
  in a full-suite run.
- **Distrust the probe before the code.** Findings that were the probe
  being wrong: reading `get_action_area()` on a dialog that keeps its
  buttons elsewhere; `AccelLabel.get_accel()`, which reports only manually
  set accelerators and so said "none" for a menu with 72; classifying every
  model-built menu item as a checkbox because they all derive from
  `GtkCheckMenuItem`.

## Specific instruments

- **xdotool drives real clicks under Xvfb**, and is the only way to learn
  what GTK actually does with a mouse button. Present the window, `wait_for`
  the layout, read the origin with
  `xdotool getactivewindow getwindowgeometry --shell`, then
  `xdotool mousemove X Y click N`, all in one process with the main loop
  pumped in between. It settled three guesses about GTK4 menus in one
  session, and confirmed that a button 2 press on a `Gtk.GridView` cell
  reaches a gesture added to the view.
- **A key press without xdotool** (fc359783, test/test_key_press.py):
  `display.map_keyval(keyval)` gives the keycode, `display.translate_key(
  keycode, state, 0)` the keyval GTK would hand over with those
  modifiers, and `window.event_handler.key_press_event(stub, keyval,
  keycode, state)` runs the real handler; patch the keybinding manager's
  `execute` to record what it is asked for.  Caps Lock is `LOCK_MASK` in
  the state; it is how the Caps Lock bug was found.
- **A pytest plugin patching `tools.atomic_write` to log a stack for any
  path under the real `~/.local/share/mcomix`** finds a test writing to the
  reader's home. The suite's own output says nothing about it. Worth
  re-running whenever a test opens a `MainWindow`.
- **`EXPLAIN QUERY PLAN` is the SQL gate**, not a duration. A plan
  containing `SCAN` on a table that grows with the library is the defect;
  assert the plan in the test. Measure at a realistic size — tens of
  thousands of books — because a quadratic path is invisible at a hundred.
- **Count what a refactor must reach before proposing it.** An `ast` walk
  for `_()` calls outside function bodies sized the interface-language
  hot-reload in one command: 257 msgids translated at import time.

## Traps this code base has sprung

- **A `_BookArea` left unclosed hangs an xdist worker.** Its thumbnailer
  thread starts as soon as the view has items and parks on a condition;
  `area.close()` in `tearDown` is not optional. The symptom is the suite
  never printing a summary while the same file passes on its own.
- **Where gdk-pixbuf's loaders are sandboxed (glycin), any gdk-pixbuf call
  that touches a file costs about as much as decoding it** —
  `Pixbuf.get_file_info()` included. A PIL header read is about 190 times
  cheaper.
- **`MComixTest` redirects `DATA_DIR` but does not create it.** Anything
  writing there must `os.makedirs` first.
- **`str.isdigit()` is not the test for what `int()` parses.** It is
  true of the superscripts (`²`), the circled numbers (`①`) and
  more, all of which `int()` refuses with ValueError. `str.isdecimal()`
  is true of exactly the Unicode decimal digits, which is both what
  `int()` accepts and what a regular expression's `\d` matches - so
  after splitting on `\d+|\D+`, `isdecimal()` is the test that agrees
  with the split. At 45eb29f9 this crashed the listing of any archive
  with such a character between two ordinary digits in a page's name.
  Two other places read the same way: version_tools._sort_key(), fixed
  with it, and pageselect's spin button, which cannot be reached because
  GTK leaves a numeric Gtk.SpinButton's text empty rather than accept
  the character.

## Text a reader typed, used as a pattern

- Every place a preference or a filter box reaches a matcher is a place
  where the text is read as a pattern unless something stops it. Find
  them with `grep -rn "LIKE\|re.compile(\|fnmatch\|glob" mcomix/` and
  ask of each where the string comes from. At 062b73d9 there were four:
  - the library's filter, which went into SQL `LIKE` unescaped, so "%"
    listed the whole library (fixed in 561d10a6 with `_contains()` in
    library/backend_types.py, which quotes `%`, `_` and the quoting
    character, and `ESCAPE '\'` on each LIKE - SQLite has no default
    escape character, so the clause is needed);
  - the "comment extensions" preference, joined with `|` into a regular
    expression, where "c++" matched "cc" and a lone "(" raised re.error
    inside FileHandler's constructor and stopped MComix starting
    (fixed in 062b73d9 with `tools.fixed_strings_regex()`, which
    escapes and sorts, and is what the format patterns already used);
  - the names handed to external unzip, which reads a member name as a
    shell pattern - archive/zip_external.py wraps `[`, `*` and `?` and
    doubles a backslash, and says so;
  - the file chooser's `fnmatch` filters, whose patterns MComix builds
    from the formats it supports, not from anything typed.
- A LIKE with a leading wildcard is served by no index either way, so
  escaping changes no query plan; test_library_types.py asserts the
  plans and passed unchanged.

## Plural strings whose count must reach every form

- `msgfmt --check` refuses a catalogue whose `msgstr[0]` leaves out a
  placeholder the `msgid_plural` carries, for the languages whose
  first form also covers 21, 31 and so on: Croatian, Lithuanian,
  Russian and Ukrainian among MComix' 24. Czech and Polish pass
  without it, their first form being for exactly one.
- So an English singular that reads better without the number - "the
  deleted book" against "the 1 deleted book" - still has to be
  *formattable* with it. Name the placeholder and format with a
  mapping: `ngettext('... the deleted book?', '... the %(count)d
  deleted books?', n) % {'count': n}`. A format string that does not
  use the key is left alone by a mapping, where `'...' % n` raises
  "not all arguments converted". book_area.py's removal messages are
  the worked example (59f23a30).

## Adding a prompt that can be answered for good

- A "Do not ask again" prompt is three things and no more: a member of
  `message_dialog.RememberedDialog` (its value is the key the answer is
  stored under in `prefs['stored dialog choices']`), an entry in
  `REMEMBERED_DIALOGS` giving the label the preferences list it by and
  the answers that may be remembered, and a call site that builds a
  `MessageDialog`, calls `set_should_remember_choice(<member>)` and
  answers in `run_async`. The preferences dialog reads the table, so
  nothing there needs touching, and `docs/Preferences.md` lists
  the prompts in prose - add it there in the same commit.
- An answer that must go on being asked is left out of the entry: a
  remembered Cancel would be a prompt that can never say yes again.
- The dialog delivers a remembered answer without appearing, through
  the idle queue, so a test pumps the main loop and then reads what the
  answer did rather than looking for a window. A test that wants a
  prompt out of the way sets `prefs['stored dialog choices'][<member>]`
  and takes it back in `addCleanup`: the preferences are one dictionary
  for the process.
- **A prompt that has to happen before something else waits for its
  answer with a continuation**, as `MainWindow._leaving_book(then)` and
  `FileActions.before_closing(then)` do: the offer runs `then()` at once
  where there is nothing to ask. Closing a book reaches the offer more
  than once (the quit asks, the file handler it closes would ask again),
  so the answer is remembered for the close with a flag that the next
  change to the book clears.
- **Two questions on the way out, and only the first can stop it.**
  `FileActions.before_closing(then)` asks the archive editor first
  (`edit_dialog.ask_before_closing`, 2e91651f) and the book's own
  unwritten changes second. The editor's answer can abandon the close -
  it runs neither `then()` nor anything after it, and clears the
  once-per-close flag so the next attempt asks again - because what the
  editor holds cannot be written from anywhere else once the book has
  gone. `MainWindow.close_program()` therefore routes the whole quit
  through `before_closing` and reports whether the quit happened while
  it ran: that is what tells its `close-request` whether the window may
  go.
- **What the editor is holding is a value comparison, not a flag**: the
  pages in order plus each comment file with the name its row carries,
  against the same tuple taken when the listing was last handed over
  (the load, Apply, a successful Save As). A flag would miss an undo
  back to where the book started.
- **Nothing can be asked from `terminate_program()`**: the main loop has
  gone by then, so a dialog there never comes back. `close_program()`
  asks first, and answers the window's `close-request` with True while
  the question is up, or the window it stands against goes.
- Tests whose window is a `mock.MagicMock` need
  `window.file_actions.has_unsaved_changes.return_value = False`: a
  MagicMock is truthy, so the close asks a question nobody answers and
  the test hangs on a book that never closes.

## A Gtk.Entry in a dialog selects all of itself

- An entry that takes the focus as its dialog is shown has the whole of
  its text selected, whatever was selected before: `select_region()`
  called while the dialog is being built is undone by the time the
  reader sees it. Pick the part out afterwards - `GLib.idle_add()` with
  a handler that selects and returns `GLib.SOURCE_REMOVE` is enough,
  since the idle runs after the dialog has been presented (a986339e's
  neighbour, 6d7911ba, is the worked example: a rename entry that
  offers the name with everything but the extension picked out).
- `Gtk.Editable.get_selection_bounds()` answers `(start, end)` in
  PyGObject, not the `(bool, start, end)` the C signature suggests.

## A new menu label needs a mnemonic of its own, per language

- `test_messages.py::MnemonicTest` fails when two items of one menu
  answer to the same Alt key, in any of the 24 catalogues, and a label
  translated from its neighbours collides often: at 613f8b96, eleven of
  the twenty-four translations of "_Copy page" took a letter the
  right-click menu had already given to "_Delete page", "_Copy" or
  another entry.
- `STATE/probes/free_mnemonic.py '<msgid>' <menu>` reads the same menus
  the test does, and for each language prints either the letter the
  label keeps or the label with the underscore moved to the first free
  letter. Apply what it suggests, compile, and read the result: a
  suggestion that lands inside a word is ordinary GTK style, one that
  lands on an article ("Copia _la pàgina") is worth moving by hand
  ("Copia la pà_gina"). CJK catalogues write the mnemonic as a trailing
  "(_P)" and rarely collide.
- The menu names are the test's: 'menu bar', 'right-click', and one per
  submenu or menu-building module.
- **Dialog buttons collide the same way and no test catches them.**
  `MnemonicTest` reads menus, not the buttons a dialog builds, so a new
  button's letter is checked by hand against the others that dialog
  shows in that language. At 3d852d50 two new buttons beside Cancel and
  OK collided in ten of the twenty-four catalogues - Russian and
  Ukrainian gave "swap" and "replace" the same letter, Lithuanian gave
  "replace" the letter Cancel had - and moving the underscore one
  syllable along was enough every time.
- **Rewording a language's menu labels moves its mnemonics.** At
  f219c5c8 thirty-five Hebrew labels went from the imperative to the
  verbal noun, and four of the new words no longer held the letter the
  old one was marked on. The loop to run: rewrite, `msgfmt`, run
  `test_messages.py`, and read the failure - it prints the whole
  {letter: label} map of the menu that clashed, which is the free-letter
  list as well. Two rounds settled it. A word whose every letter is
  taken is the sign to move the *other* label's mnemonic instead
  ("מעבר" had no free letter, so Preferences gave up ע).
- **One msgid used in two menus carries one mnemonic for both.** Reusing
  a label rather than adding a string is the right trade - at 48793054
  the archive editor took the window's "Re_name page..." - but the
  letter then has to be free in both menus, and the probe checks one
  menu at a time. Take the union of the taken sets before choosing, and
  be ready for a language where nothing is left: Hungarian had no free
  letter across the two and needed different words ("Új név
  megadása..."), which is allowed, since a translation is not a
  transliteration.

## Changing the pages of the open book

- Every edit to the book in the main window goes through one shape, in
  `FileActions.remove_pages()`: read the listing with
  `imagehandler.get_image_files()`, push a copy of it onto `_undone`,
  clear `_redone`, change the list, and hand it to `_show_pages()`,
  which calls `MainWindow.pages_replaced()`. Undo and redo are whole
  listings, so any edit expressible as a new list of paths - a
  removal, a swap, a reordering - costs nothing extra to make
  undoable, and `offer_to_save()` is what asks to write the archive.
- `MainWindow.selected_pages` is the set picked out with Ctrl and a
  click, drawn with the CSS class `MainWindow._SELECTED_CLASS`; an
  interaction that marks pages for something else (a swap) needs a
  look of its own rather than that set.
- What a save does to the names is fixed: `Packer._files_to_pack()`
  writes each page as `<number> - <book name><extension>`, numbered in
  the order of the listing with as many digits as the count needs, so
  the *order* of an edit survives a save and the *names* do not
  (documented for readers in ac76ea66).
- **`imagehandler.get_image_files()` hands out a copy**, so an edit has
  to change the list it then passes to `_show_pages()`. A second call
  answers with the book as it still is, and the change made to the
  first copy is dropped on the floor. This broke `_rename_on_disk()` at
  3d852d50 for exactly one commit.
- **Two files that change names with each other are followed in one
  pass.** `FileActions._paths_changed(listing, moved)` walks the drawn
  listing and both undo stacks once with a dict of old path to new one;
  two calls, one per file, turn the first file into the second and then
  the second back into the first.
- **One dialog asks for every name, at 37c6f5d5**: `rename_dialog.ask()`
  builds the entry, the warning line and the answers a clash leaves, and
  `rename_dialog.read(current, typed)` is the rule that turns what was
  typed into a name (basename, old extension where none was typed, None
  where nothing changed). A caller gives it a `clash` callable, asked as
  the reader types, which answers a `Clash(told, answers)` - `answers`
  False where the thing holding the name cannot be swapped or removed
  from that list, which hides both buttons and leaves Cancel. The
  editor's comment list renames through the same call (38fa1a0e), and
  its rows carry the name, so the editor's own undo covers it.
- **A comment file is renamed only in the editor**: `Packer` takes
  `comment_names` beside `page_names`, and the editor's Save As passes
  `_CommentArea.file_names()`. The window's own save knows nothing of
  it, exactly as it knows nothing of a comment removed there - the
  editor applies only its page listing to the window. A ComicInfo.xml
  is moved out of the comments into the carried files before the packer
  sees it, so it keeps its name whatever the list says.
- **Who is called what, at 3d852d50**: `page_name(page)` is the name a
  page will be written under - `_page_names[path]`, or the basename of
  its file; `name_typed(page, typed)` normalises what a reader types
  (basename, extension kept, None where it says nothing new);
  `page_called(name, other_than)` finds the page holding a name. A
  rename inside an archive is a line in `_page_names` until the book is
  written; a rename in a folder of images is `os.rename` at once. The
  packer's underscore for a taken name is now the last resort it was
  meant to be: the dialog offers a swap or a replace first.

## Adding a keyboard action

- A key that does something new is registered as an action, never read
  out of a key handler: the reader can then rebind or clear it in the
  Shortcuts tab, and the loop's own sweep ("the keybinding table and
  event.py's registrations match exactly") stays true. Four places, all
  in one commit (798eb5e0 is the worked example):
  - `keybindings.py` `BINDING_INFO`: `'name': {'title': _('...'),
    'group': _('...')}` - the title is a new translatable string;
  - `event.py` `_register_keybindings()`: `manager.register('name',
    ['Menu', '<Shift>F10'], <callable>)`, where each default is a string
    `Gtk.accelerator_parse()` understands (check it: it answers
    `(True, keyval, mods)`);
  - `docs/Keybindings.md`, in the table the function belongs to;
  - the catalogues, as any new string.
- A handler that a key reaches has no pointer position to work from, so
  anything that reads one needs an answer of its own: the page menu's
  `popup_page` becomes the page on screen rather than the page under
  the pointer, and `widgets.popup_at()` is given the middle of the page
  area.

## What follows a book that moves or goes

- MComix records a book's path in five places, and each one has to be
  brought forward when "Move to" moves the file (see
  `FileActions.move_current_file`):
  - the library, `backend.LibraryBackend().update_book_path()`;
  - the store of last read pages, whose old entry is cleared;
  - the bookmarks, `BookmarksStore.update_path()` (3a7612d7);
  - the recent files, whose old entry is removed while reopening the
    book records the new one (917cf8fe);
  - the "moved to before" destinations, which hold the folder rather
    than the book and need nothing.
  Deleting the file instead forgets the path in the recent files
  (42ed9bbc) and clears the last read page; the bookmarks and the
  library entry are left standing, because removing a reader's
  bookmark is not something a delete should do quietly.
- The pattern to check when anything new records a path: grep for the
  five, and ask which of them the new code has to tell.

## Translations

- **Two new strings cost a template regeneration and 24 catalogues.**
  `test/test_messages.py::TemplateTest` fails until `mcomix/messages/mcomix.pot`
  holds every marked string, so the catalogue work lands in the same commit as
  the strings. The procedure is in `docs/Maintenance.md`: `xgettext`
  over `mcomix/*.py mcomix/archive/*.py mcomix/library/*.py`, then
  `msgmerge -U --backup=none` each `.po`, then `msgfmt` each one to its `.mo`,
  which is committed. `msgfmt --statistics -o /dev/null` on every `.po` is the
  check that they are all complete; run `msgmerge` once more after filling the
  new entries, to rewrap them the way gettext would.

- **`msgmerge -U` writes nothing when no message changed**, so a catalogue
  keeps its old `POT-Creation-Date` and whatever wrapping the last hand edit
  left it with. A release regeneration wants both refreshed: merge with
  `msgmerge -q -o <temp> <po> <pot>` and move the temporary file into place,
  which is what gives gettext's own wrapping. At ac8209e2 that rewrapped the
  message 2e91651f had added as one long line in twenty-one catalogues.
- **`msgfmt` leaves `POT-Creation-Date` out of the `.mo`.** A regeneration
  that only moves that date therefore leaves every compiled catalogue byte
  for byte what it was, and `git status` listing no `.mo` is itself the proof
  that no translation changed. The finer check is `msgcat --no-wrap` over the
  committed and the new `.po`, diffed with the date line grepped out: it
  normalises wrapping and keeps comments, references and flags, so a fuzzy
  mark or a lost translator comment would show.
- **A release commit regenerates the template with the new version**
  (`--package-version` comes from `mcomix/constants.py`, so bump the version
  first), then merges every catalogue against it. `mcomix.pot` then differs
  from the previous release only in `Project-Id-Version` and the date when no
  string changed in between.

## Working in this repository

- **Every bug fix gets a regression test you have watched fail.** Write it,
  copy the fixed file aside, `git checkout HEAD -- <file>`, confirm the test
  fails, copy back, confirm it passes.
- **Never `git stash`.** The stash stack belongs to the repository, not to a
  worktree, and other sessions share this one. Copying files aside does the
  same job safely.
- **Never `git commit --amend`** (the guard refuses it): an amend issued
  moments after a hand commit landed once rewrote the user's commit with the
  loop's message. A wrong commit is fixed forward.

## Finding what one test leaves for the next

- **MComixTest now fails the test that leaves a window visible**
  (`_no_window_left_on_screen`, e7e4bdcd). A cross-test failure where a
  test counts dialogs it never opened should no longer happen; if one
  does, the leak is in something that becomes visible after cleanup, such
  as an idle callback or a GTK dialog raised asynchronously.
- **A pytest plugin passed with `-p <module>` (the module on PYTHONPATH)**
  can walk `Gtk.Window.list_toplevels()` after each test and print the
  labels inside what is still visible, recursing with `get_first_child()`
  and `get_next_sibling()`. The labels identified GTK's own "Operation was
  cancelled" chooser error, and a `GtkTooltipWindow` among them named a
  directory in the real home, which is how the chooser preference default
  was found (5a9a9d96).
- **Do not compare `id()` of PyGObject wrappers across calls** to tell old
  windows from new: `list_toplevels()` may hand back a fresh wrapper for
  the same window, so a before/after `id()` set reports it twice.
- **GSETTINGS_BACKEND=keyfile with XDG_CONFIG_HOME in a scratch directory**
  shows whether a run writes GSettings, without touching the real dconf
  database. Check it takes effect first: `Gio.Settings(...).props.backend`
  is a `GKeyfileSettingsBackend`, and a `set_int` plus `Gio.Settings.sync()`
  creates `glib-2.0/settings/keyfile`. The mtime of `~/.config/dconf/user`
  proves nothing: nautilus and VS Code write it all the time.
- **A GTK file chooser destroyed before the main loop turns once shows
  GTK's "The folder contents could not be displayed" dialog**, over any
  folder. One pump before destroying is enough.
- **The file chooser's preview follows the chooser's selection, not
  `_previewed`.** A 200 ms poll compares `filechooser.get_file()` with
  `_previewed` and clears the preview when nothing is selected, so a probe
  that sets `_previewed` and calls `_update_preview()` by hand is undone
  within a fifth of a second and reports a cleared preview whatever the
  code does. Select with `widgets.set_chooser_file(dialog.filechooser,
  path)` and wait for the poll instead.

## Sweeps that found work

- **Comments narrating the GTK3 port**:
  `grep -nE "^\s*#.*(used to |There (was|were) |was only ever|GTK3|Gtk\.Table|Gtk\.EventBox|Gtk\.Layout|went with|is gone|no longer )" mcomix/**/*.py`
  over every tracked file. It over-matches ("no longer" is often present
  tense, and a docstring explaining why a class exists is fine), so read
  each hit with a few lines of context. Check any claim a comment makes
  about what GTK does before rewriting it into the present tense: one
  said a scrolled window recomputes the adjustments, and the widget is a
  custom `PageCanvas` that does it in `_configure()`.
- **Private names reached across objects**:
  `git grep -n "\.[a-z_]*\._[a-z]" -- mcomix` and, per name,
  `git grep -nw <name> -- mcomix test` to size it. A leading-underscore
  attribute or method used from another module is either an interface
  that should lose the underscore or a sign the caller wants a coarser
  method. Rename with `sed -E 's/\b_name\b/name/g'` over the named files
  and confirm with `git grep -nw _name` that nothing is left, including
  strings in tests that patch the method by name.

## PyGObject introspection traps

- **`GObject.signal_list_names(<PyGObject class>)` answers `()` for every
  class**, `Gtk.Button` included, so it cannot show that a widget has no
  signals. Ask for one by name with
  `GObject.signal_lookup('file-activated', Gtk.FileChooserWidget)`, which
  answers 0 for a signal the type does not have; check the probe against a
  signal that certainly exists (`'clicked'` on `Gtk.Button`) first. It
  showed that GTK4's `Gtk.FileChooserWidget` keeps its keybinding signals
  (`location-popup`, `up-folder`, `show-hidden`) while a comment said it had
  none at all; what it lacks is `file-activated` and `update-preview`.

## Sweeps that found work (continued)

- **Port narration the first sweep misses**: comments that name GTK4 to
  contrast it with what GTK3 had. `grep -nE "^\s*#.*(GTK ?4|in GTK|is gone|
  went with)"` over tracked files, then read each: "GTK4 has no X, so Y"
  states a constraint the code still works under and stays; "X is gone in
  GTK4", "X is Y in GTK4" and "the old handler sat there" narrate the port
  and go. Past tense in a comment next to a fix ("used to leave", "the
  closure held one and the timer went on") is the same kind of narration
  and is rewritten into what the code must do and why.
- **Every `except Exception` in mcomix/, read one by one** (38 at
  ba358e90; `grep -rn -B6 -A4 "except Exception" mcomix/` into a file
  under SCRATCH). All but one are deliberate and say so in a comment:
  decoder fallbacks in image_tools, worker threads that log because
  nothing joins them, a corrupt file read at start-up. What the sweep
  is looking for is the handler over an operation the *user* asked for
  and is watching: file_actions._save_page_to() logged a failed "Save
  page as" and nothing more, so the chooser closed and no page
  appeared. Still open, same shape: library/book_area.py's
  _remove_answered() logs a book it could not delete from disk while
  the entry is gone from the library, so the reader is told the file
  was deleted when it is still there.

- **Activating a stateful boolean `Gio.SimpleAction` that has only a
  `change-state` handler asks for the opposite of its state**: a bare Gio
  probe (`new_stateful('x', None, GLib.Variant('b', False))`, connect
  `change-state`, `activate(None)`) delivers True. So a toggle whose state
  has fallen out of step with the preference it stands for makes the next
  keyboard activation set the preference to what it already is. No MComix
  import is needed, so nothing can reach the real home.

- **Text read in the machine's encoding**: an `ast` walk for `open()`
  calls whose mode has no `b` and whose keywords have no `encoding`
  (over `mcomix/**/*.py`). At 11c6d882 there were four. Three read JSON
  that `json.dump` wrote with its default `ensure_ascii`, so the files
  on disk are pure ASCII and no encoding can change what comes back -
  hygiene, not a bug, and not worth a commit that proves nothing. The
  fourth read a comment file out of an archive, which is whatever its
  author wrote: it raised UnicodeDecodeError, was caught, and the
  Comments dialog said "Could not read" instead. `i18n.to_unicode()` is
  what this code base decodes unknown bytes with (chardet where
  installed, then the locale, the file system encoding, UTF-8, Latin-1,
  and UTF-8 with replacements), and a test proves the fix by writing a
  Latin-1 comment into a zip with `ZipFile.writestr()`, which takes
  bytes. The same sweep over `subprocess` found every external archiver
  already passing `encoding='utf-8'`, and `bytes.decode()` with no
  argument is UTF-8 rather than the locale, so it is not a finding.

## Checking what the port changed

- **Upstream's `mcomix/ui.py` holds the GTK3 menus as UI XML.**
  `git show origin/master:mcomix/ui.py | grep -c menuitem` counts 95, and
  `grep 'menuitem action="<name>"'` answers whether an action ever had a
  menu item. Prove the probe on an item that certainly had one
  (`enhance_image`) before trusting a miss. It showed that `invert_color`
  was reachable only by Ctrl+I and the enhance dialog before the port too.
- **Actions no layout lists**: walk `mcomix/ui.py` with `ast` for the first
  string argument of every call inside a `self._actions.add*(...)` call,
  and for every string constant in `_MENUBAR`, `_POPUP` and `_TOOLBAR`;
  the difference is the candidates, and a radio group's own name
  (`autorotation`) is among them by construction.
- **Preferences nothing reads**: take the keys of the `_DEFAULTS` dict
  literal in `mcomix/preferences.py` (an `AnnAssign`) and search every
  other tracked `.py` for the quoted key.
- **Signals the GTK3 tree connected**, the same sweep one level up:
  `git -c color.ui=false grep "connect" 0128281 -- 'mcomix/*.py' |
  grep -oE "connect(_after)?\(['\"][a-zA-Z0-9_-]+" | sed "s/.*['\"]//" |
  sort | uniq -c | sort -rn`
  (`git grep` colours its output, and the escape sequences break a
  `grep -o` on the same line, hence `-c color.ui=false`). At 4ce10ef7
  that was 45 distinct signals; all but three have a counterpart. The
  three: `popup-menu`, which GTK emitted for the menu key and for
  Shift+F10 and the port answered with a `Gdk.KEY_Menu` check in each of
  the two library areas (4ce10ef7 added the other key);
  `key_release_event`, whose whole body set
  `imagehandler.force_single_step`, which nothing in 0128281 ever read -
  dead upstream, not lost in the port - and `connect-proxy` /
  `disconnect-proxy`, the `TooltipStatusHelper` that showed a menu
  item's tooltip in the status bar: Gtk.MenuItem and its `select` signal
  are gone, GTK4 menus are popovers built from a Gio.Menu, and nothing
  there says which item the pointer is over.
- **GTK's own keyboard conventions are readable from a live widget.**
  A class's shortcuts are installed on it, so a throwaway instance lists
  them: walk `widget.observe_controllers()` for the
  `Gtk.ShortcutController`s and print `shortcut.get_trigger().to_string()`
  with `shortcut.get_action().to_string()`. A `Gtk.Text` answers
  `<Shift>F10 action(menu.popup)` and `Menu action(menu.popup)`, which
  is how 4ce10ef7 proved that a context menu is asked for by two keys
  and not one. This is evidence a reading of GTK's C source cannot beat,
  because it is the version installed here.
- **Behaviour the port set as a widget property** is invisible to a
  reading of the new code, because what is missing is a line that was
  never written. Sweep the GTK3 tree for the setters that carry
  behaviour rather than looks:
  `git grep -n "set_activate_on_single_click\|set_reorderable\|set_enable_search\|set_search_column\|set_tooltip_column\|set_headers_clickable\|set_selection_mode" 0128281 -- 'mcomix/*.py'`
  and check each against its port. At c7f7aad8 that was nine calls in
  five files; eight had a counterpart (bookmark_dialog's reorder, search
  and sortable headings; edit_image_area's tooltip, reorder and multiple
  selection; book_area's multiple selection; openwith's reorder), and
  the one that did not was the thumbnail sidebar's
  `set_activate_on_single_click(True)` - a click on a thumbnail no
  longer turned to its page. The GTK4 spelling is
  `Gtk.ListView.set_single_click_activate()`, whose documented meaning
  is wider than the GTK3 property: "Activate rows on single click **and
  select them on hover**" (from `/usr/share/gir-1.0/Gtk-4.0.gir`, which
  carries the doc strings PyGObject's help does not). Where a selection
  means something - in the sidebar it is the page being read - the
  hovering has to be answered, here by a `Gtk.EventControllerMotion`
  whose `leave` puts the highlight back.

## A page is listed before its file is there

- `imagehandler.get_number_of_pages()` answers as soon as the archive
  has been listed, which is a different moment from the page's file
  being on disk: the extractor runs on a thread of its own. A test that
  waits only for the listing and then reads `get_path_to_page(1)` gets
  a path that may not exist yet. At 36d7c297 that failed about one run
  in eight - two in fourteen runs of the file on its own, never under
  the whole suite, where the neighbours give the extractor time.
  `wait_for(lambda: handler.page_is_available(1))` is the wait that
  says the file is there; `page_is_available()` with no argument asks
  about the page on screen.
- This is what the recorded re-check command in LOOP_NOTES is for: the
  flake was found by re-running the previous iteration's own claim,
  which had printed "4 passed" when it was written.

## Building the book a test needs

- **An archive of any awkward shape is three lines in `setUp`**:
  `zipfile.ZipFile(os.path.join(self.tmp_dir, 'x.zip'), 'w')` and
  `writestr()` for each entry. A zip holding only `readme.txt` opens, is
  listed, and reaches `_archive_opened()` with no images, which is the
  state where `ImageHandler.get_current_page()` answers 0 while the file
  handler counts the file as loaded. `test/files/archives` has no such
  archive, and a crafted file is faster to read in a test than a binary
  fixture.
- **`get_current_page()` answers 0 for "no page"**, and code that stores or
  indexes by it has to say what 0 means. `git grep -n "get_current_page()"
  -- 'mcomix/*.py'` lists every reader; the one that stored 0 filed an
  unread archive in the library (ad74c94c).

## Coverage

- **pytest-cov 7.1 and coverage 7.15 are installed, and a covered run of
  the whole suite takes about 22 s under -n 8**, within the probe
  timeout. Keep the data file out of the repository:

  ```sh
  COVERAGE_FILE=<scratchpad>/.coverage env -u WAYLAND_DISPLAY GDK_BACKEND=x11 \
      timeout 60 xvfb-run -a python3 -m pytest test/ -q -n 8 -p no:cacheprovider \
      --cov=mcomix --cov-report=term-missing:skip-covered > <scratchpad>/cov.txt 2>&1
  grep -E "^mcomix/\S+\s+[0-9]+\s+[0-9]+\s+[0-9]+%" <scratchpad>/cov.txt |
      awk '{print $3, $4, $1}' | sort -rn
  ```

  The missed-lines column points at code no test runs, which is where a
  sweep for bugs pays best: scrolling.py at 26% was the space bar's whole
  algorithm.

## Property probes for pure code

- **A seeded `random.Random` over a few thousand generated inputs, with
  each invariant counted by kind and the first two failures printed,**
  checks an algorithm faster than reading it. Generate only inputs the
  callers can produce, and prove each alarm against that before believing
  it: the first smart-scrolling probe reported 1495 "unread gaps" because
  it allowed steps longer than the viewport, which the caller never asks
  for (event.py sizes a step as a fraction of the viewport), and a
  "never finished" because its step cap was below the 132 x 38 stops the
  page had.
- **Smart scrolling's two directions are mirror images, not one grid.**
  Reading back from the far corner stops at `end - p` for every stop `p`
  reading on from the near corner takes; `_bresenham_sums(n, d, True)` is
  the mirror of `(n, d, False)`. A test that expects a step back to retrace
  the stops exactly is wrong one time in about fifty.
- **A test that bites only on inputs already on the grid misses the
  between-grid branch.** Breaking `index -= 1` in `scroll_smartly()` failed
  none of five stop-list tests; a start at a position a step back leaves
  (51 on a [0, 50, 101] grid) is what reaches it. When a deliberate break
  passes, that is a missing test, not a harmless break.
- (at b36bab11) STATE/probes/mirror_scroll.py <tree> checks the mirror
  property of `scroll_smartly()` over 20,000 random pages, viewports,
  steps and positions, including positions before and past the page:
  reading backwards from the mirrored position must land on the mirror
  of reading forwards.  It found 21 mismatches on f32d62f2 - a `>` where
  the forward test's mirror needs `>=` - and none since.  A mirror or
  inverse property is the cheapest oracle for code like this: no
  expected values to work out, and the reading of a comparison that
  differs by one character between the two directions is exactly what
  it catches.

## Listeners that outlive what they belong to

- **A destroyed MComix dialog is not collected, even by `gc.collect()`.**
  The handlers `connect()`ed to its own widgets hold the Python object,
  so the weak reference `callback.CallbackList` keeps to a bound method's
  object never dies, and a dialog that subscribed with `+=` and never
  `-=` goes on running for the rest of the session. 'destroy' never comes
  for the same reason; 'unrealize' does, and is where to unsubscribe
  (c9d0b9ce, efe3ebc5, fc1787da).
- **The sweep that finds a missing `-=`**: walk every `mcomix/**/*.py`
  with a regular expression for `<target>.<event> += ` and `-= `, count
  each event per file, and print the files where the two disagree. At
  d76e3177 that listed 29 events; all but one belong to an object that
  dies with the window (the menus, the thumbnail bar, the main window,
  the image handler) or are a plain `+=` on a string or a number
  (`name`, `_search_typed_so_far`, `current_size`). The one that
  mattered was `bookmark_dialog.py`, which subscribes to four callbacks
  of the store and unsubscribed from three - the fourth had been added
  one iteration earlier.
- **A test for this proves the handler did not run, not that nothing
  crashed.** Closing the dialog and asking the store to do the thing
  the handler answers must leave the dialog's own rows as they were;
  counting rows is not enough when the handler removes one and adds
  another, so compare what the rows hold.
- **Count what is still subscribed rather than guessing**: a
  `Callback`-decorated method becomes an instance attribute after the
  first `+=`, so `owner.__dict__.get('page_changed')` is the
  `CallbackList`, and `lst._CallbackList__callbacks` is a list of
  `(weakref or None, function)`. Resolve each weakref and count the ones
  that are instances of the dialog class, after opening and closing it
  twice and `gc.collect()`. Two per callback is the leak.
- **A regression test for such a leak patches a method the handler
  reaches through `self.` at call time** (`_update_image_page`,
  `_add_comment`, `get_command`, `histogram.draw_histogram`). Patching the
  subscribed method itself does nothing, because the list captured the
  plain function when it was subscribed. Check that the handler's own
  early returns do not stop it first: the library's cover view returns
  before `add_books()` unless a collection is selected, and the first
  version of its test passed on HEAD for that reason.
- **Sweep**: `git grep -n "+= self\._" -- 'mcomix/*.py'` beside
  `git grep -n "-= self\._"`. What subscribes to something that lives
  longer than itself (the window, the file or image handler, the library
  backend) needs a matching `-=`; menus and sidebars that live as long as
  the window do not.

## A worker that aborts inside GTK

- **"worker 'gwN' crashed" with "Fatal Python error: Aborted"** and a C
  stack of `gtk_window_destroy` → `gtk_widget_unrealize` →
  `gsk_renderer_unrealize` → `g_assertion_message_expr` is a GSK renderer
  assertion under Xvfb, not MComix code. It took down
  `test_library_dialog.py::WatchListScanTest::test_closing_an_edited_watch_list_scans_the_library`
  once in four full runs at c9d0b9ce, and three runs of a clean export
  passed. The tests set no `GSK_RENDERER`. Record the stack and rerun on
  an export before blaming a change; the Python stack names only the line
  that destroyed a window.

## Threads that share one thing

- **One sqlite3 connection shared by threads fails without a lock, even
  with `sqlite3.threadsafety == 3`.**  sqlite3 caches prepared
  statements per connection, and two threads running the same text at
  once step the same statement.  A bare probe of four threads making
  two point lookups a round for two seconds got 13,177 errors in 87,726
  rounds ("bad parameter or other API misuse", "another row
  available", and silent None answers).  `cached_statements=0` stops
  it at 50-85% more per statement; a lock held from execute to cursor
  close stops it at 4-11% (e36960a9).  The backend's execute(),
  fetchone() and fetchall() hold that lock; a new statement must go
  through them, never through `_con`, and a listener must never be
  called while the lock is held (the lock is not reentrant).
- **Make a race deterministic by parking the worker inside the slow
  call.**  Patch the module attribute the code calls at run time
  (`image_tools.load_pixbuf`) with a function that sets one Event and
  waits on another; start the thread, wait for the first Event, do the
  main-thread action, set the second, join.  The 00a test in
  test_image_handler.py is the model.
- **Stand in for an archive handler by wrapping the real one** after
  the extractor has listed it: an object whose `__getattr__` delegates
  and which overrides `is_solid()` and `iter_extract()`.  `close()` still
  reaches the real archive through the delegation.
- **A real solid pass that fails:** `os.chmod(destination, 0o555)` before
  `extract()` makes the 7z handler raise PermissionError on its first
  file.  Restore the mode before the temporary directory is removed.
- **Library covers in a real window:** `_LibraryWindowTest` from
  test_library_dialog.py, `dialog.backend.add_book()` for a handful of
  test archives, `prefs['library cover size'] = 50` (below 50 the cover
  worker never asks for the page read), then `book_area.display_covers(None)`
  and count `item.thumbnail is not None` over `book_area._each_item()`.
  Patch `mcomix.log.error` to collect what the worker threads log.

## Sharing master with the PR-prep session

- **Commit with `git commit -F <message> -- <paths>`.**  It commits
  those paths as they are in the working tree and nothing else, whatever
  another session has modified or staged.
- **Gate on an export:** `git archive HEAD | tar -x -C <dir>`, copy your
  changed files in, run the three gates there.  The working tree may
  hold the other session's uncommitted catalogues or version bump.
- **ChangeLog.md's 4.0.0 section is written for readers upgrading from
  3.2.**  A fix goes into the "Among the long-standing ones" sentence
  only if origin/master has the bug too (`git show origin/master:<path>`
  settles it); a bug in code this branch added gets no line.  Keep the
  section near 50 lines.

## Which thread reaches something, across the whole suite

- **A pytest plugin on PYTHONPATH answers "can a thread other than the
  main one ever do X" better than reading call sites.**  Install the
  patch in `pytest_runtest_setup` the first time it runs, not in
  `pytest_configure`: by then the test modules have imported mcomix the
  way they mean to, and importing it earlier from a plugin risks
  resolving the constants against the real home.  Write what it sees to
  a file per pid (xdist workers load `-p` plugins too), count the
  main-thread hits as well so an empty result is shown to be a working
  probe, and run it on an export:
  `PYTHONPATH=<scratchpad> xvfb-run -a python3 -m pytest test/ -n 8 -p <module>`.
  It showed 876 library backend openings or requests with none open,
  every one on the main thread.
- **Patch a module-level factory, not a name bound at import.**
  `backend.LibraryBackend` is looked up at call time by every caller
  (`get_backend()` imports it inside the function), so replacing the
  module attribute reaches them all.

## The recently-used list in a probe

- **`Gtk.RecentManager.add_item()` records nothing without a program
  name.**  It fills the entry's application name from
  `g_get_prgname()`, and a bare script or the test harness has none, so
  GTK prints "no name of the application that is registering it was
  defined" and drops the entry; `add_item()` still returns True.
  `run.py` calls `GLib.set_prgname(constants.APPNAME)`, which is why the
  real program's Recent list works.  A probe that wants MComix' own
  `RecentFilesMenu.add_path()` to land calls `GLib.set_prgname('mcomix')`
  before anything else; tests use `add_full()` with a `Gtk.RecentData`
  instead, as `test/test_recent.py` does.  Redirect the manager too
  (`Gtk.RecentManager(filename=<temp>)` behind a patched `get_default`),
  and turn `gtk-recent-files-enabled` on and `gtk-recent-files-max-age`
  up on `Gtk.Settings`, since a bare X server defaults to keeping
  nothing.
- **The store and the program name are the harness's now** (1dbe0a91,
  add07972). `test/__init__.py` sets `GLib.set_prgname(APPNAME)` at
  import, as run.py does, and hands every test one
  `Gtk.RecentManager` in the session's temporary directory behind a
  patched `get_default`, purged in `setUp`. Before that, the default
  manager was built inside whichever test opened a window first and went
  on writing into that removed directory - 333 "no name of the
  application" warnings and about 20 "Attempting to store changes"
  warnings per run, plus a rare `OSError: [Errno 39] Directory not
  empty` when a write landed inside another test's `shutil.rmtree`.
- **GTK's warnings are invisible without `-s`.** pytest captures each
  worker's stderr and prints it only for a failing test, so a warning
  that costs nothing visible hides for months. The sweep is
  `pytest test/ -q -n 8 -s > <log> 2>&1` and then
  `grep -oE "(Gtk|Gdk|GLib)-(WARNING|CRITICAL) \*\*: .{0,70}" <log> |
  sed -E 's/[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+//' | sort | uniq -c |
  sort -rn`. At add07972 what is left is two "Finalizing ... but it
  still has children left" (a popover menu on a list view, a thumbnail
  grid) and one `gtk_root_get_focus: assertion 'GTK_IS_ROOT (self)'
  failed` per run; no MComix code calls either function.
- **The suite does not reach the reader's own list** (checked at
  917cf8fe): GLib resolves `XDG_DATA_HOME` when the default manager is
  built, and `MComixTest` sets that variable before any window exists,
  so the entries land in the test's temporary home. Proved by setting
  `HOME` and `XDG_DATA_HOME` before importing `gi`, calling
  `add_full()`, and running a main loop until
  `<temp>/data/recently-used.xbel` appears - it takes a second or two,
  because GTK batches the write, so a probe that checks straight away
  sees nothing and concludes the opposite. The manager is a singleton
  for the process, so every later test in a worker writes into the
  first test's temporary home, which is gone by then; GTK swallows
  that.

## The native PDF handler's worker processes

- **A probe that opens a PDF through `FitzArchive` and then calls
  `os._exit(0)` leaves the manager's process behind** - and, where the
  start method is forkserver (Python 3.14's default on Linux), the
  forkserver and the resource tracker too, all reparented to PID 1.
  `os._exit` skips the finalizer that shuts a `BaseManager` down, and the
  orphans keep the command's stdout pipe open, so the Bash tool waits for
  an end of file that never comes and the command looks hung.  Close the
  archive's manager (`archive._mgr.mgr.shutdown()`) before `os._exit`, or
  end with `sys.exit`, and list `ps -eo pid,ppid,args | grep forkserver`
  afterwards; kill leftovers by PID, never with `pkill -f`, whose pattern
  matches the tool's own shell.
- **What the worker sees depends on the start method.**  A forked worker
  inherits the parent's preferences; a forkserver or spawned one imports
  `mcomix.preferences` afresh and sees the defaults.  Anything the worker
  needs from the reader's settings has to be passed to it.
- **Measured on cf4dc21c, Python 3.14, PyMuPDF 1.28.2, GTK loaded first:**
  importing `pdf_multi` 275 ms (PyMuPDF itself about 220 ms of it); the
  first `page_count()` 260 ms under forkserver and 12 ms under fork.
  `probes/bench_pdf_open.py`-style: build the PDF in a separate process
  first, so the parent's own PyMuPDF import is not what is measured.
- **Forkserver on Python 3.12 and 3.13 listens on a socket file, whose
  path Linux caps at 108 bytes.**  The test harness puts TMPDIR inside
  the checkout (`test/tmp/session.*`), so the suite run from a deep
  directory - a scratchpad export such as
  `/tmp/claude-1000/<project>/<uuid>/scratchpad/export-x/` - fails every
  test that opens a PDF through the worker with "OSError: AF_UNIX path too
  long", while the same tree in `/tmp/mcomix-pr` passes.  Python 3.14
  uses abstract sockets and is not affected.  Run the 3.12 floors
  environment from a short path.
- **Floors environments are cheap to build here.**  `uv python install
  3.12`, then `uv venv --python 3.12 <dir>` and `uv pip install --python
  <dir>/bin/python 'PyGObject==3.46.0' 'pycairo==1.25.0' 'Pillow==10.1.0'
  'PyMuPDF==<v>' chardet pytest pytest-xdist` builds against the system's
  GTK 4 and gobject-introspection headers in under a minute.  Swap one
  package's version per copy to bisect which floor a failure belongs to.
- **Correction to the entry above about the socket path:** the deep
  directory was not the cause, or not the only one.  `MComixTest` points
  `tempfile.tempdir` at a directory named after the module, the class and
  the test method, and multiprocessing works its temporary directory out
  once per process, the first time a manager or forkserver needs one - so
  it landed inside the first such test's directory.  A probe measured the
  listener path at 172 bytes from `/tmp/mcomix-pr` itself, against
  Linux's 108, and that directory is removed when the test ends.
  `test/__init__.py` now calls `multiprocessing.util.get_temp_dir()` on
  import, inside the session directory, as it pins GLib's.  A new pinned
  process-wide cache of a temporary path is the thing to look for when a
  test passes alone and fails after a sibling.

## The wiki tooling under wiki/src

- **This whole section is history (corrected at ec577bb5).** The pages
  moved to `docs/` as GitHub Markdown and `wiki/` was deleted with them:
  `wiki/src/sfwikisync`, `wiki/Readme.md`, `test/test_sfwikisync.py` and
  the conversion half of `test/test_wiki.py` are gone. What is left of
  `test_wiki.py` checks the pages under `docs/` against the program, with
  `ROOT`/`DOCS` at its top and an `IMAGE_LINK` regular expression in place
  of the converter's `images()`. The notes below describe code that no
  longer exists; they are kept because the mutation driver, the rendering
  check and the locale trap apply to anything under `docs/` as well.
- **test/ loads wiki code without installing it.** `test_wiki.py` loads
  `wiki/src/sfwikisync/github.py` by file with
  `importlib.util.spec_from_file_location`, which works because that module
  imports nothing from its package.  `test_sfwikisync.py` imports the whole
  package with `sys.path` and `sys.modules` patched (`mock.patch.dict`), a
  stand-in `requests` module in place: MComix does not depend on requests and
  CI does not install it.  The stand-in's `get`/`post` raise, so a test that
  forgets to patch them cannot reach SourceForge.  `patch.dict` removes the
  imported `sfwikisync.*` entries again on exit; check with
  `[m for m in sys.modules if m.startswith(('sfwikisync', 'requests'))]`.
- **Mutation driver.** `<scratchpad>/mutate.py`-style: a list of
  `(file, exact old text, new text, name)`, assert the old text occurs once,
  write, run one test file in a subprocess under xvfb-run, restore in a
  `finally`.  One process per mutation, about 0.5 s each for a small file.
  `git status --short` afterwards proves every file came back.
- **Rendering check for Markdown.** `cmark-gfm -e table page.md` (and
  `pandoc`, `cmark`) are installed.  Count `<h[1-6]` against the source's
  headings, grep the HTML for leftover markup, list `href`/`src`.
- **SourceForge's wiki API, read without a token** (a GET of
  `https://sourceforge.net/rest/p/mcomix/wiki/<Page>`): keys `_id`,
  `attachments`, `discussion_thread`, `discussion_thread_url`, `labels`,
  `mod_date`, `related_artifacts`, `text`, `title`.  `text` has CRLF line
  endings and keeps a trailing CRLF as pushed; `labels` is `['']` on pages
  with none; a missing page is HTTP 404.  Never POST: that publishes.
- **Watching an encoding fix fail on a UTF-8 machine.** A bare `open()` uses
  the locale's encoding, which cannot be patched in-process (the C code reads
  it directly).  Run the test file under
  `env LC_ALL=C PYTHONUTF8=0 PYTHONCOERCECLOCALE=0` - all three, or Python
  coerces the C locale to UTF-8 - and `locale.getencoding()` is
  `ANSI_X3.4-1968`: a missing `encoding="utf-8"` then fails on any non-ASCII
  text, as it would under a Windows code page.  Keep such a test file free of
  GTK imports so it runs on its own.

## Patching a dependency's version

- **`PIL.__version__` patched before `PIL.Image` is imported makes the import
  itself fail.** `PIL/Image.py` compares `__version__` with its C extension's
  on first import and raises ImportError on a mismatch.  A test of
  `run.setup_dependencies()` that patches the version then exits through the
  "no Pillow found" branch, and passes for the wrong reason - it did, on the
  unfixed code, until `import PIL.Image` moved to the test module's top.
  Run a version-check test alone (`-k`) on HEAD as well as fixed: in the full
  suite something else has usually imported the module already, which hides
  this.

## Checking a label the documentation quotes

- **A substring of the module's source is not a label.** `test_wiki.py`
  checked quoted dialog labels with `label in source.replace('_', '')`, and
  renaming the "Automatically adjust contrast" check box still passed: its
  tooltip repeats the words.  Compare with the module's translated strings
  instead - `translated()` over `ast.walk(parse_module(module))`, underscores
  removed, a trailing colon or ellipsis stripped - and prove it by renaming
  the `_('...')` argument alone.  Short labels ("OK", "Save") cannot be
  looked for on a page at all: they occur inside other words.

## Singletons that remember the first window

- **`bookmark_backend.BookmarksStore` and `keybindings.keybinding_manager()`
  are one per process, and each keeps the first window it was given.**
  On an xdist worker that window belongs to whichever test built one first,
  so a test of a second window gets bookmarks added through a stub image
  handler, or accelerators announced to another window's menus.  A test
  passed alone and failed in every `-n 8` run.  Reset them before the window
  is built (`keybindings._manager = None`, as `MainWindowTest.setUp` does)
  or, for the store, `_initialized = False; _bookmarks = []` then
  `initialize(window)`.
- **Reproducing a worker's order.** `pytest -k 'a or b'` runs in file
  order, not in the order the names are given, and so did not reproduce it.
  Pass node ids instead: `pytest file::Class::test_first
  file::Class::test_second -v` runs them in that order.
- **Gio does not run a disabled action**, however it is activated:
  after `set_enabled(False)`, neither `Gio.SimpleAction.activate(None)` nor
  `Gio.SimpleActionGroup.activate_action(name, None)` calls the handler.  A
  first probe printed a running call count, 1 before and 1 after disabling,
  and was read the wrong way round; e650b1c7 went in with a redundant
  `get_enabled()` check and a message saying the opposite.  Make a probe
  print the answer to its question ("ran the handler: False"), not a
  number to interpret, and treat a mutation that fails nothing as evidence
  against the claim, not as noise.

## Folding follow-up commits into a curated series

- **Which curated commit a follow-up can fold into without conflicts:** the
  last curated commit that touches any of its files, or a later one.  Map
  it with `git show --name-only --format= <commit>` over
  `origin/master..<last curated>` into {path: [commit numbers]}, then take
  the maximum over each follow-up's paths.  At 840793a2, 8 of 21 follow-ups
  folded cleanly on theme; the rest touched ChangeLog.md, the catalogues or
  files of the version-bump commit itself.  The written review is
  /tmp/mcomix-push/recuration-review.md.
- **Screenshots:** `/tmp/mcomix-push/screenshots/screenshots.py <outdir>`
  under `xvfb-run -a -s '-screen 0 1920x1080x24'`, from /tmp/mcomix-git;
  about 15 s.  It opens test/files/pepper-and-carrot at pages 2-3 and files
  it in the library.  View the PNGs before replacing the published ones.

## Screenshots, catalogue terms and menu layouts

- **Shrinking the screenshots:** `pngquant --speed 1 <name>.png` writes
  `<name>-fs8.png`, a 256-colour palette image; move it over the original,
  since the wiki attachments keep their names.  At 186de239 it took
  mcomix-mainwindow.png (1280x800, painted comic pages) from 1,083,626 to
  386,294 bytes, the library from 17,172 to 5,899 and the external commands
  dialog from 40,548 to 14,299.  Checked with PIL and numpy against the
  original: mean absolute channel difference 1.4 on the main window (99th
  percentile 13, all in the dithered art), 0.006 and 0.018 on the dialogs;
  a 2x nearest-neighbour crop of both side by side showed no difference.
- **Which word a catalogue should use for a term:** GTK's own catalogue for
  the language, `msgunfmt /usr/share/locale/<lang>/LC_MESSAGES/gtk40.mo |
  grep -i -A1 'msgid "[^"]*bookmark'`, settles it with a source the
  translators of that language agreed on.  Count both spellings over the
  catalogue's live (non-`#~`) msgstr lines first; the fix is usually the
  minority.  test_messages.TermTest holds the dropped spellings per
  language and reads the compiled .mo, so it needs no xgettext.
- **Mutating ui._MENUBAR with sed** also hits the right-click popup layout
  below it, which repeats the Toolbars submenu line for line: check
  `git diff --stat mcomix/ui.py` shows what was meant to change, and restore
  with `git checkout HEAD -- mcomix/ui.py` only after confirming the file
  was clean before the mutation (`git diff --quiet mcomix/ui.py`).

## Re-cutting a curated series (folding later commits in)

- **Build forward with `git cherry-pick --no-commit`, not rebase.** In a
  worktree of its own on `pr/<name>`, reset to the last curated commit that
  stays, then for each new commit cherry-pick every source with
  `--no-commit` (the index need not match HEAD) and commit once.  After a
  conflicted pick, resolve and run `git cherry-pick --quit` before the next
  one.  The script of 2026-09-13 is kept at
  /tmp/claude-1000/<project>/<uuid>/scratchpad/recut.py.
- **A follow-up can depend on another follow-up**, which a map of the last
  curated commit touching each file misses: df6ba852's test called
  comicinfo.describe(), which a35d41d7 (not folded) added, and appended to
  a file a35d41d7 had changed.  Before folding one, list the earlier
  follow-ups touching its files and read its tests for names they added.
- **Leaving the version bump out of the commits after it:** force
  ChangeLog.md back to the tree before the bump after every pick
  (`git checkout HEAD -- ChangeLog.md`); for a source that regenerated the
  catalogues take its whole `mcomix/messages` and put the template's
  `Project-Id-Version` back to the development version (the .po files keep
  their own).  Check each commit: ChangeLog blob equal to the pre-bump one,
  VERSION and metainfo without 4.0.0, and `git diff -U0 <last catalogue
  source> <new> -- mcomix/messages` showing only the header line.
- **Checking a rebuilt commit against the original it stands for:** the
  files `git diff --name-only <original> <new>` lists must be inside the
  files of the commits one of the two trees has and the other has not
  (original: everything up to it in the old order; new: everything picked
  so far).  The last commit reads master's tree whole, and
  `git diff --quiet master <tip>` proves nothing was lost.
- **Rewording after gating:** rebuilding only to change messages keeps the
  trees; compare `git rev-parse <old>^{tree}` with the new ones position by
  position, and the gates already run still hold.
- **Gating 24 trees:** one export and one fake home per commit
  (`.config/mcomix`, `.local/share/mcomix` created), sequential, in the
  background; about 70 s each with a cold mypy cache.
- **Second sighting (2026-09-13):** the same C stack
  (`g_assertion_message_expr`, `gsk_renderer_unrealize`,
  `gtk_widget_unrealize`, `gtk_window_destroy`) aborted worker gw1 in
  `test_main_window.py::MainWindowTest::test_the_right_click_menu_saves_the_page_it_was_opened_over`,
  once in about 30 full runs that day, on a tree whose code four other
  runs passed.  Grep the pytest log for `gsk_renderer_unrealize` to tell
  it from a crash of MComix' own.
- **Folding a commit made on master into an older commit of the series:**
  commit it on master first and gate it there, then rebuild from the
  commit before the one it joins: `cherry-pick` each later commit as it
  is (keeps author and message), and for the target `cherry-pick
  --no-commit` the target and the new commit, then commit with the
  target's author (GIT_AUTHOR_NAME/EMAIL/DATE from `git log --format=%an
  %ae %ad --date=raw`).  Check: trees before the target unchanged, each
  later tree differs from its original exactly in the new commit's files,
  the last tree equals master.  Only the changed trees need gates.
  (fold_images.py in the 2026-09-13 session scratchpad.)
- **Rebuilding a series on a new upstream commit that rewrites code the
  series also changed:** do not cherry-pick through the conflicts.  Take
  each commit's tree whole (`git read-tree -u --reset <commit>`) and
  rewrite only the files the upstream commit touches with a function
  that applies its change, then commit with the original message and
  author.  Make the function prove itself: applied to the upstream
  commit's parent it must give the upstream file byte for byte, and any
  removal of a series commit's own change must give that commit's parent
  file.  Check each new tree differs from its original only in the
  rewritten files.  (onto_upstream.py, 2026-09-13 session scratchpad.)
- **Fetching the project's repository without a remote:** `git fetch
  https://git.code.sf.net/p/mcomix/git refs/heads/master:refs/remotes/upstream/master`
  works where SourceForge's web pages answer scripts with 403.
- **Another flake of the middle of the curated series:** at "feat: Use
  libadwaita, and add a theme preference",
  `test_password_dialog.py::PasswordDialogTest::test_the_password_reaches_the_caller`
  finds a Gtk.MessageDialog still visible after the prompt answered, in
  about half the full `-n 8` runs, and passes alone.  Same family as the
  file chooser flake: a window one test left reaching the next, fixed by
  the harness later in the series.
- **Moving a checked-out branch with `git update-ref`** leaves its index
  and files at the old tree.  Harmless when the trees are equal; when they
  differ, `git status` then shows the old contents as staged changes.
  Check the unstaged diff is empty and the staged one is exactly
  `git diff --name-status <new> <old>`, then `git read-tree -m -u <old>
  <new>`, which refuses rather than overwrites local changes.
- **Setting a JPEG's Exif orientation without compressing it again:**
  walk the segments from SOI to SOS (`FF xx` plus a big-endian length
  that counts itself; RSTn and TEM have none; `FF FF` is fill), drop an
  existing `APP1 "Exif\0\0"` after loading it into `Image.Exif()`, set the
  tag, and write `FF E1` + length + `exif.tobytes()` (which starts with
  "Exif\0\0" in Pillow 12) after a JFIF APP0, then everything from SOS on
  as it was.  Test it by comparing the bytes from `FF DA` on, before and
  after; a flat test image compressed again at the same quality can come
  out byte-identical, so use `Image.effect_noise` and quality 95.
  (native_pdf/child.py, jpeg_with_orientation.)

## GTK's renderer under Xvfb

- **Xvfb has no DRI3, so GSK refuses GL ("renderer is llvmpipe") and falls
  back to its Vulkan renderer in software.**  `GSK_DEBUG=renderer` prints
  the choice; `window.get_native().get_renderer()` after a `present()` and
  a few turns of the main context names the class.  Measured on GTK 4.22.5
  at 1812037d: the suite takes 22.2-22.5 s on that renderer and 14.4-17.6 s
  with `GSK_RENDERER=cairo`.  `test/__init__.py` sets cairo with
  `setdefault` since eb0657f0, so a renderer named in the environment still
  wins; a probe not built on `test/` should set it too, for speed and to
  stay clear of the Vulkan renderer's unrealize assertion.

## What the guard reads, and what a `cd` does

- **The guard reads the command's text but not heredoc bodies** (corrected:
  earlier guards read them too, and a commit message that mentioned
  "xvfb-run" or "rm -rf" was refused). Writing a message to a file and
  passing `git commit -F <file>` still works and keeps the command short.
- **`cd` into a subdirectory moves the session's working directory**
  (the harness reports "Primary working directory: ... (was ...)"), and it
  stays there for later commands. Do not `cd`; pass paths relative to the
  checkout or absolute, and address the campaign worktree with `git -C`.
- **`git grep` colours its output here even into a pipe**; use
  `git --no-pager grep --no-color` when the output is grepped or cut.

## Sweeping the catalogues without polib

- polib is not installed.  Splitting a `.po` on blank lines and joining the
  quoted pieces of `msgid` and `msgstr` with
  `''.join(re.findall(r'"(.*)"', group))` is enough for a sweep; skip
  blocks containing `#~`.  Sweeps that found work: log messages ("! ...")
  whose msgstr equals the msgid (Hebrew kept six), and msgstrs that lose
  the msgid's "X: Y" colon or add ".:" or " :" outside French (six, in
  ja/ko/it/he).  The "!" prefix is dropped by some fr/ja/ru/sv log
  messages and written full-width by zh; both are harmless and were left.
- **`msgmerge -U` does not rewrap an entry whose content did not change
  semantically**, so a hand-edited long msgstr stays on one line.  Write
  the merge to a file with `-o` and copy it over the catalogue instead;
  that output is what gettext's own wrapping gives.

## Copies of a checkout

- **Copying a worktree directory copies its `.git` file**, which points at
  the real repository: git run in the copy moves the real branch.  Use
  `gates.sh --export` (a `git archive`) or `git worktree add` for a tree
  of your own.
- **A hand-written check for failures must not match "12 xfailed"**: grep
  for `(^| )[0-9]+ failed`.

## New strings: merge without fuzzy matching

- **`msgmerge` fuzzy-matches a new msgid to an old one it resembles and
  copies that translation in, marked fuzzy.**  "! Could not scan for new
  books: %s" arrived in the Catalan catalogue carrying the translation of
  the cover-fetching error.  When adding a string whose translations are
  written by hand, merge with `msgmerge -N -U --backup=none <po> <pot>`,
  fill the empty msgstr, then merge again with `-o` to a temporary file to
  get gettext's wrapping, and compile.  `msgfmt --statistics` should then
  count one more translated message and no fuzzy ones.

- **A new string whose neighbour is already translated**: when the
  string mirrors one that exists ("Could not save X to Y" beside
  "Could not move X to Y"), print every catalogue's translation of the
  neighbour first, then write each new entry by keeping that sentence
  and changing the verb. Quotation marks differ by language in those
  translations - guillemets in Catalan, Galician, Greek, Russian,
  Ukrainian, Persian and French (spaced), low-high in Czech,
  Lithuanian, Croatian and Hungarian, plain in the rest - and copying
  the neighbour keeps each one's own. At ba358e90 two strings across
  24 catalogues took one pass this way, with every catalogue at 634
  translated messages and none fuzzy.

## The suite's own warnings are a sweep

- **`grep -oE '[A-Za-z]+Warning' SCRATCH/pytest.txt | sort | uniq -c`**
  after a gates run lists the categories the suite raised; anything other
  than DeprecationWarning deserves a look.  It found a thread whose
  exception escaped (`PytestUnhandledThreadExceptionWarning`, with the
  test's name on the line above) and a dead ini option in test/pytest.ini
  (`PytestConfigWarning: Unknown config option`).  To prove a change
  leaves collection alone, diff the `::` lines of a `--collect-only -q`
  run before and after.

## Correction: GSK's Vulkan renderer here is the GPU, not software

- The entry "GTK's renderer under Xvfb" above says the Vulkan renderer
  runs in software.  It does not on this machine: `GDK_DEBUG=vulkan`
  lists one device, "NVIDIA GeForce RTX 5070 Ti (Discrete GPU)", and GSK
  uses it ("Using Vulkan device 0").  Only GL is software (llvmpipe),
  which is why GSK turns GL down.  The cairo renderer is still the faster
  one for the suite: on a clean export of 69c7a989, 8.9-10.7 s against
  14.7-17.6 s with `GSK_RENDERER=vulkan`.  Check a claim about what
  hardware a library uses with its own debug output before writing it.

## GTK's own warnings during the suite

- **pytest captures what GTK prints, and shows it only for a failing
  test.**  Run the suite with `-s` (it still works under `-n 8`: the
  workers' stderr reaches the terminal) into a file, then
  `grep -oE 'Gtk-WARNING[^:]*: .*'` and group with `sort | uniq -c`.  At
  69c7a989 it printed 236 Gtk-WARNINGs: most are "Attempting to add ...
  to the list of recently used resources, but no name of the
  application" (the tests set no application name) and "Attempting to
  store changes" from a test that makes its directory read-only; the two
  structural ones were a GtkWindow finalized with a GtkPopoverMenu still
  parented (test_widgets, fixed in b332fc17) and a notebook tab strip
  reporting min height -3 (test_comment_dialog, a scrollable notebook
  emptied of pages).
- **To find which file prints a warning**, run every file on its own,
  eight at a time, inside one Xvfb: STATE/probes/perfile.sh does it with
  `xargs -P 8`, one log per file under SCRATCH/perfile/, and takes about
  as long as the suite.  Then `-v -s` on that file: the warning prints
  between the PASSED lines of the tests around it.
- **A pytest inside a quoted `sh -c "..."` loop passes the guard when a
  `timeout` wraps the whole string** (corrected: earlier guards refused it).
  A loop in a script under `STATE/probes/` run as `timeout -k 5 <s>
  xvfb-run -a sh <script>` is still the more readable form.

## One translation serving two messages

- **A msgstr shared by msgids that say different things is usually a
  translation copied from the neighbouring entry.**  Group each
  catalogue's entries by msgstr, normalise the msgids (drop `_ . … :`,
  trailing space, case), and list groups with more than one msgid whose
  msgstr is longer than 25 characters or holds a `%`.  At b332fc17 it
  found six real slips (388cdb2b) and three harmless pairs ("Fit size
  mode"/"Fit to size mode" in cs, el, lt; "View mode"/"View modes" in it).

## Sweeps that came back empty (at 53ddcbf9)

- Preferences defined in mcomix/preferences.py and never named elsewhere
  in mcomix/: none of 198 keys ("config format version" is read inside
  preferences.py).
- `except Exception: pass` in mcomix/: two, both deliberate fallbacks from
  Pillow to gdk-pixbuf/glycin in image_tools (file_animates,
  get_image_header).
- Thread bodies that let an exception escape: only the watch-list scan,
  fixed in 53ddcbf9; worker_thread, page_image's decoder, the thumbnailer
  and archive_packer all catch and log.
- test/run.py is a working pytest wrapper (MCOMIXPATH, -k shorthand), not
  dead code.
- Correction at 7caaae87: archive_packer's pack thread could still let a
  second exception out of its `finally: archive.clean_up()`; fixed in
  71a0c6f7.
- (at fc359783) Also came back empty: `locale.getdefaultlocale` raises
  no DeprecationWarning on Python 3.14; `Win32Popen` is Windows-only and
  was left alone (only its docstring was stale); `openwith`'s preview
  quoting is MComix' own command syntax, so `shlex.join` would be wrong;
  the shortcuts editor records "N" under Caps Lock, which
  `Gtk.accelerator_parse()` reads back as n; `offer_column_chooser`'s
  bound-method callback does not keep the bookmarks dialog alive
  (test_dialog_freed passes); the editor areas find their editor through
  a weak reference because a test injects a stub, not through
  `get_root()`; widget "survivors" of a close in test_zz_measure (two
  per open) are a probe artefact, `GOBJECT_DEBUG=instance-count` shows
  none.

## Why a closed dialog is never collected, and what it costs

- **GTK 4 does not dispose a destroyed window's widget tree.**
  `gtk_window_destroy()` hides, unrealizes and drops GTK's own reference;
  the children stay parented.  A child widget's C reference from its
  parent makes PyGObject's toggle reference strong, so its wrapper and
  the closures connected to it are roots to Python's GC, and a closure
  holding a bound method of the dialog keeps the dialog alive.
  `Gtk.CallbackAction.new(self._x)` is worse: it holds the callable
  through a destroy-notify, which PyGObject never traverses (Dialog's
  Escape shortcut, the archive editor's undo and redo).
- **Measure it with a probe on MComixTest**:
  STATE/probes/probe_editor_leak.py opens and closes the editor CYCLES times on
  BOOK and prints RSS, the live `_EditArchiveDialog` count and the live
  `ThumbnailItem`s with a thumbnail; REFERRERS=1 lists what refers to a
  leaked dialog (bound methods named by `__func__.__qualname__`, dicts by
  the class owning them).  STATE/probes/probe_library_leak.py does the library
  window.  STATE/probes/big60.cbz is a 60-page 1200x1800 JPEG book for it.
  Count objects, not only RSS: freed memory is not always returned to the
  system, and the count is what the fix changes exactly.
- **`run_dispose()` over the whole tree is not a fix**: GTK prints
  "Gtk-CRITICAL: GtkStack ... has a parent GtkNotebook during dispose"
  (and the same for a GtkRange's gizmos), and the CallbackAction roots
  survive it.  Breaking the cycle for good means disconnecting handlers
  and replacing CallbackActions with ones that hold the dialog weakly, in
  every dialog: a campaign, for the user to open.  Until then, a dialog
  with heavy content lets go of it on close (fa97fb56: the editor's
  thumbnails and undo snapshots).
- (corrected at 84f240b8: the user has since moved the probes named
  above into STATE/probes/, so they are there after all.)  Another
  instrument is
  `test/test_dialog_freed.py` (campaign branch loop/dialog-leak): it
  opens each dialog through the main window's actions, finds the new
  toplevel, closes it, collects, and on failure names the holders with
  `_holders()` (bound methods by qualname, closures by owning function,
  instance dicts by owner class).  Run it against master's code with
  `MCOMIXPATH=/tmp/mcomix-git` from the worktree to see what still leaks
  there.  Build its failure message lazily: `gc.get_referrers` in an
  eagerly formatted assert message made every passing test take 13 s.
- **What works** (loop/dialog-leak, 60323f18..84506084; landed squashed
  as aa498a4f, and the branch commits named here are gone): after the
  window's own unrealize (`connect_after`), disconnect every handler
  with NULL user data on each descendant widget and each event
  controller of the window and its descendants:
  `GObject.signal_handlers_disconnect_matched(obj,
  GObject.SignalMatchType.DATA, 0, 0, None, None, None)`.  PyGObject
  connects every Python handler with NULL data; GTK's own nearly all
  carry data.  `signal_handlers_destroy()` or `remove_controller()` on
  the window's controllers instead gives Gtk-CRITICALs
  (gtk_shortcut_set_trigger, g_list_model_get_item) and a
  g_object_unref warning when the objects are finally freed.
  Top-down `run_dispose()` after `set_child(None)` was worse still:
  gtk_range_get_adjustment criticals and more dialogs leaking.
- **What the sweep cannot reach**, each fixed per dialog: handlers on
  non-widget objects GTK holds (a selection model, an adjustment:
  `Dialog.connect_while_open()`); a child widget subclass holding the
  dialog in an attribute (a parented child's wrapper is a GC root, so
  its `__dict__` is too: hold the dialog through `weakref.ref`); list
  view factories, sorters and bound cells (`widgets.Releasable`,
  `ColumnListView.release()`); `Gtk.CallbackAction` callbacks (a module
  function or unbound method called on the widget GTK passes in).
- **GTK unbinds list rows lazily.**  After `set_model(None)` the
  factories' unbind runs later, after the handler sweep, and a cell's
  `disconnect(id)` then warns "instance has no handler with id".  Under
  xdist that GLib warning (class `gobject.Warning`, module `gobject`)
  cannot be unserialised and kills the worker ("node down ... import
  static modules like gobject", INTERNALERROR).  Find the test with
  `-W "error::gi._gi.Warning"`; `-p no:warnings` hides it.
  (at a9aaba96) For a crash that comes once in many runs, `-W error` may
  not catch it: a warning raised while the collector finalizes an object
  is not raised in any test.  Print instead: `-p no:warnings -s` with
  `PYTHONWARNINGS=always::Warning`, output to a file, then grep for
  `Warning: ../glib`.

## The library backend singleton between tests

- `backend.LibraryBackend()` is one per process and a `FileHandler` opens
  it as it is built (`LastReadPage`); only `terminate_program()` closes
  it.  A test that builds a handler over a mock window leaves it open on
  a database in its own removed temporary home, and the next test on the
  worker that writes to the library fails with "sqlite3.OperationalError:
  attempt to write a readonly database" - in setUp, so its tearDown never
  closes it and the whole class fails after it.  Since 7caaae87
  `MComixTest._no_library_left_open` fails the test that leaves it open.

## Coverage points at bugs (at 16cc1188)

- **The least-covered modules held three real bugs in one sweep**:
  mobi.py at 26% could not list a book at all (StopIteration from an
  extension-less gdk-pixbuf format, and Gio guessing nothing on Windows;
  916d02f6), file_chooser_library_dialog.py at 32% crashed the process
  after its dialog closed (48150817), slideshow.py at 45% swapped the tool
  bar's icon for a smaller full-colour one (4300e3e3). Run the covered
  suite (section "Coverage"), sort by percentage, and read the bottom
  five before anything else. A module no test imports at all is the best
  bet: the first test that merely opens the thing is often the one that
  fails.
- **A binary format is quicker to build in the test than to ship**:
  test/test_mobi.py writes a Palm database (78-byte header, 8-byte record
  index, records) with struct in twenty lines.

## GTK reference counts, from Python

- **`obj.__grefcount__` reads a GObject's reference count**, so a bare
  GTK script can show whether a call balances its references: a count
  that turns to garbage (3545088429) means the object was freed while
  Python still holds it, and the next `gc.collect()` segfaults.
  GTK 4.22.5 with PyGObject 3.56.3: `Gtk.FileChooserWidget.remove_filter()`
  frees the filter it removes, current or not; add/remove of a CSS
  provider for the display balances. STATE/probes/probe_remove_filter.py.
- **A segfault in teardown under pytest shows as "Fatal Python error:
  Segmentation fault" and rc 139**, with the Python stack printed; the
  frame is often `tools.garbage_collect`, which only finds the damage.
  Bisect the setup in a probe on MComixTest with a `gc.collect()` between
  steps (STATE/probes/probe_libchooser.py).

## Icons

- **`Gtk.Button.set_icon_name()` replaces the button's child** with a new
  image of the default size; the tool bar's buttons carry a Gtk.Image at
  `Gtk.IconSize.LARGE`, so change that image instead.
- **Which theme answers for an icon**:
  `Gtk.IconTheme.get_for_display(d).lookup_icon(name, None, 16, 1,
  Gtk.TextDirection.LTR, 0).get_file().get_path()`. Adwaita ships only
  symbolic icons; a name without "-symbolic" is answered by AdwaitaLegacy
  in full colour, or not at all where that theme is not installed. Only
  the tool bar reads the icons ui.py names (`_actions.icon()`); the menus
  show none.

## Plural forms in the catalogues

- **Turning `_('%d things')` into `ngettext()`**: edit the code, regenerate
  the template (Maintenance.md's xgettext line), `msgmerge -q -N -U
  --backup=none` each catalogue, fill `msgstr[0..n-1]` by script for each
  language's `nplurals` (STATE/probes/fill_plurals.py checks the count
  against the header), then `msgmerge -q -N -o <tmp>` (no `--backup`
  with `-o`) and copy back for gettext's wrapping, and `msgfmt --check`.
  Prove the forms with `gettext.GNUTranslations(open(mo, 'rb')).ngettext`
  over 0, 1, 2, 5, 12, 21, 22. Hungarian and Persian take the singular
  after a numeral, so both forms are the same there.
- The reference lines of every message below an edited line move, so
  such a commit touches all 24 catalogues by thousands of `#:` lines;
  count the other changed lines to see what really changed.
- **A new plural message is written from the neighbour that already has
  one.** Print every catalogue's forms for a message counting the same
  noun - "Removed %d book from the library." is the one for books -
  with a `re` search over `msgid ...\nmsgid_plural[^\n]*\n((?:msgstr
  \[\d\][^\n]*\n)+)`, and write each new form by keeping that
  language's noun and case and changing the verb. It is the only way to
  get Czech "knihu/knihy/knih", Polish "książkę/książki/książek" and
  Lithuanian "knygos/knygų" right without knowing the languages. The
  counts at 05cdbdcb: one form for id, ja, ko, zh_CN and zh_TW; three
  for cs, hr, lt, pl, ru and uk; two for the rest, with hu and fa
  repeating the singular.
- **Filling by position, not by regular expression**: find the
  `msgid`/`msgid_plural` pair, then walk the `msgstr[n]` lines that
  follow it and assert their number against the translations to be
  written. A catalogue whose `nplurals` disagrees then fails loudly
  instead of being filled wrongly.

## Probes that measured the wrong thing (at 71a0c6f7)

- STATE/probes/probe_library_leak.py closed the library with
  `main_dialog._close_dialog()`, which skips `_LibraryDialog.close()` and
  with it `book_area.close()`; every real path goes through `close()`.
- STATE/probes/probe_editor_leak.py counted the main window sidebar's
  ThumbnailItems with the editor's and its page wait returned at once;
  STATE/probes/verify/probe_editor_leak2.py takes the tree as a parameter,
  waits on the grid's store and counts the editor's items apart.
- **A `cd` inside a Bash command moves the session's working directory**
  for later commands; it happened twice here. Use `git -C` and paths from
  the checkout; never `cd`.

## Widgets a freed window leaves behind (C-cycles inside the tree)

- **A popover stays on the widget it opened over.** `widgets.popup_at()`
  parents a menu the first time it is shown and nothing takes it off,
  so GTK finalized the widget with the menu still there: "Finalizing
  MComixColumnListView, but it still has children left: GtkPopoverMenu".
  `widgets.release()` now unparents them (1c414c1a) - but only the ones
  `popup_at()` parented, kept in a weak set: GTK builds popovers of its
  own inside its file chooser, and unparenting those left the chooser
  tripping over what was missing, three "gtk_tree_view_set_model:
  assertion 'GTK_IS_TREE_VIEW (tree_view)' failed" per run. Any sweep
  that walks a window's tree and changes what it finds has to ask the
  same question: whose widget is this?
- **A freed window is not a freed tree.**  Once the window finalizes,
  its child is unparented but any subtree whose widgets reach each other
  through C stays: a child class with an action group inserted on it
  (the group holds actions, the actions hold the child's methods), a
  list view's factory whose handlers are the view's own methods, drag
  controllers on cells, a selection handler of the parent held by a
  child view's selection.  Check with weak_ref on every widget, not on
  the window alone: STATE/probes/test_zz_measure.py (copy into the
  worktree's test/, delete afterwards) opens a dialog twenty times and
  prints windows and widgets finalized, the surviving widget types and
  the RSS growth.  At 84f240b8: editor 1360 of 1440 widgets freed
  (640 before), library 800 of 1080 (560 before).
- **A GObject whose wrapper is gone still holds its Python handlers,
  and nothing traverses them.**  A `Gio.SimpleAction` created, connected
  and added to a group, with no Python reference kept, makes its
  handler a GC root for as long as the group lives.  Taking the group
  off the widget is enough only when nothing else keeps the group; an
  area that also keeps it as an attribute has to empty it
  (`widgets.empty_action_group`).
- **A list view keeps cells aside for rows to come, outside the widget
  tree**, so a sweep of the tree misses their controllers.  The views
  track what their factories built in a `weakref.WeakSet` and cut those
  cells' handlers in `release()` (`widgets.cut_handlers`).
- **Tracing a survivor**: gc.get_objects() filtered by type name, then
  walk gc.get_referrers() a few levels, skipping frames, iterators and
  the referrer lists the walk itself made; print `__grefcount__` of each
  GObject met.  A wrapper at g1 is weak and collectable; one at g2+ is a
  root (something in C holds its object), and the chain ends where a
  bound method has no Python referrer: its closure is held in C.

## Plural forms: a plain message turned into ngettext()

- (at cb5d0b06) `msgmerge -N` leaves the new plural entry empty and the
  old translation as an obsolete `#~` entry.
  STATE/probes/fill_plural_from_obsolete.py copies the old translation
  into every form and removes the obsolete entry, except for the
  languages whose forms it gives in FORMS (edit FORMS for each message).
  Run it with the old and the new plural msgid, then rewrap with
  `msgmerge -q -N -o <tmp>` and compile.  A translation built as
  "new books: N" (hr, lt, ru, uk here) fits every number unchanged.
- Check that nothing else moved: the obsolete `#~` line count of each
  catalogue against `git show HEAD:<po>`, and the `-U0` diff with the
  `#:` reference lines filtered out.  msgmerge also drops translator
  comments attached to the replaced entry (eight GTK 2-era
  "# File: src/library.py" lines went this time).
- A regression test needs no window: call the unbound method on a stub
  (`main_dialog._LibraryDialog._new_files_found(stub, files, entry)`)
  with `i18n._translation` patched to a `gettext.GNUTranslations` read
  from the committed `.mo`.

## Private names reached across modules: an AST sweep

- (at de191da4) `ast.walk` over every file under mcomix/, keeping each
  `Attribute` whose `attr` starts with one underscore and whose value is
  not `self`, `cls` or `super()`, lists every reach into another object's
  or module's private name with its first file:line.  Grep cannot do it:
  git grep colours its output, so `grep -v self` on it filters nothing.
  What it found at 46f4d43c and was fixed: a stdlib private function
  (`gettext._expand_lang`), a private helper called from two modules,
  two private attributes written from outside, one private module
  global read from two modules.  What is left is module-private
  classes (`backend_types._Book` and the like) used by their sibling
  modules: a naming convention, not a defect.

## The dynamic background colour: benchmark and test page

- (at ebc12ff4) STATE/probes/bench_edge_colour.py times
  `image_tools.get_most_common_edge_colour()` against any MComix tree
  (first argument; `git archive HEAD mcomix | tar -x -C <dir>` gives the
  old one) on the images named after it, median of 30 calls.  The test
  pages big60.cbz holds have too few colours to exercise the grouping;
  a noisy scan does: 1200x1800 RGB, `random.seed(1)`, every pixel
  (232, 228, 215) plus `randint(-6, 6)` per channel, clamped.
- A page one pixel wide makes both edges the same column, so a test
  can set the exact colour counts the function sees (EdgeColourTest).

## A page turn, timed and profiled

- (at 4bd8e7e2) STATE/probes/test_zz_page_turn.py opens big60.cbz in a
  MainWindow on MComixTest, waits until all 60 pages are extracted,
  turns 30 pages one at a time (each drawn before the next) and prints
  the median and worst wall time per turn and a cProfile of the run
  restricted to mcomix, by cumulative time.  PROFILE=0 times without
  the profiler.  At 4bd8e7e2: median 5.6 ms, max 9.7 ms; load_pixbuf and
  the thumbnail bar's selection are the largest shares.  It measures
  turns into pages already cached; a cold turn would have to wait for
  the extractor instead.
- (at 45eb29f9) Re-measured: median 4.7 ms, max 10.6 to 13.5 ms over
  three runs - no regression since 4bd8e7e2, and the thumbnail
  sidebar's single-click activation (c7f7aad8) costs nothing.
- **The profile covers the worker threads too**, which is why
  get_thumbnail() has the largest cumulative time although the sidebar
  makes its thumbnails on a WorkerThread: since Python 3.12 cProfile
  goes through sys.monitoring, which is process-wide rather than one
  thread's.  So cumulative times there are not the latency of a turn -
  the wall-clock median is - and `print_callers()` is what says which
  thread a line belongs to.  PROFILE=0 used to fail the probe, because
  pstats refuses a profiler that never ran; fixed in the saved copy.

## Every SQL statement the suite runs, explained

- (at 4bd8e7e2) STATE/probes/sqltrace_plugin.py wraps `sqlite3.connect`
  so every connection records its statements (expanded, with values)
  to `$SQLTRACE_DIR/<pid>.sql`; run the suite with
  `PYTHONPATH=STATE/probes SQLTRACE_DIR=<dir> ... pytest test/ -n 8
  -p sqltrace_plugin` (make the directory with `rm -rf; mkdir`: zsh
  aborts a `&&` chain on an `rm` glob that matches nothing).
  STATE/probes/sql_plans.py <dir> rebuilds the schema in memory from the
  traced CREATE statements, folds literals so one statement counts once,
  and prints every statement whose plan scans a table, with how often
  the suite ran it.
- At 4bd8e7e2: 21,304 statements, 101 distinct, 28 that scan.  None is
  a defect: they scan collection, watchlist, recent or lastread (small,
  or read once at a migration), or they are listings of the whole
  library that are meant to be whole ("All books", the scan's list of
  known paths, the filter's LIKE).  Rerun after any change to
  backend.py, backend_types.py or last_read_page.py.

## A cold page turn

- (at 06ab4e28) STATE/probes/test_zz_cold_turn.py opens big60.cbz and,
  as soon as page 1 is available, jumps to pages the extractor has not
  reached, timing each until available.  At 06ab4e28: first page 71 ms
  after the window was built, page 50 with 2 of 60 extracted 45 ms.
- A GLib warning under xdist: since 8622a34a test/conftest.py makes
  gobject.Warning importable in the controller, so such a warning is
  listed in the summary with its test instead of killing the worker.
  Grep the gate log for `Warning: ../glib` after a run.

## Property checks that found bugs in the geometry code

- (at f3c31d0c) STATE/probes/properties.py <tree> checks three
  properties over 20,000 random cases each - remap_axes undone by
  inverse_axis_map, scroll_to_predefined's mirror, Box.intersect and
  bounding_box being commutative and bounding - and all three hold.
  Mutating the code (centring without the direction, an inverse that
  returns its input) makes it report thousands of mismatches, so it is
  worth re-running after a change to tools, box or scrolling.
- **Ask what a docstring promises and check that instead of an
  example.**  `_scale_distributed()` says it brings the total as close
  to the limit as whole pixels allow; a loop over random page sets
  comparing the summed widths against the limit found a case that
  overshot (a page already one pixel wide cannot give up another, and
  each page was only ever taken down once - f3c31d0c).  The same shape
  of check found the smart-scrolling mirror bug at b36bab11.  Keep such
  a check in the suite with a fixed seed and a couple of thousand cases,
  which costs tens of milliseconds.

## GTK's own documentation, offline

`/usr/share/gir-1.0/Gtk-4.0.gir` carries every doc string GTK's
introspection data was built from, and answers what a property or method
actually promises when PyGObject's `find_property(...).get_blurb()`
returns None (it does for most of GTK 4.22). Properties appear once per
class, so find the class first:

    awk -v L=<line> 'NR<=L && /<class name=/ {c=$0} NR==L {print c; exit}' \
        /usr/share/gir-1.0/Gtk-4.0.gir

after `grep -n 'name="single-click-activate"'` has given the lines. The
`filename=` attribute on each `<doc>` names the C file it came from,
which tells ListView's copy from GridView's and ColumnView's.

## Where the documentation lives, and what checks it

- **The manual is `docs/*.md` in GitHub Markdown** since ec577bb5, with
  the screenshots in `docs/images/` and an index in `docs/README.md`.
  The repository's own `README.md` is its front page: what MComix is, and
  what this fork adds on top of upstream 3.2.  There is no wiki, no
  Allura markup and no sync tool any more, so a page is edited in place
  and nothing has to be pushed anywhere.
- **`test/test_wiki.py` is the accuracy gate.**  It compares
  `Preferences.md` with every label and tab `preferences_dialog.py`
  builds (and with the obsolete messages in the catalogues, so an option
  the program dropped cannot stay on the page), `Documentation.md` with
  the defaults and the menu labels it quotes, `Installation.md` and its
  dependency floors with `pyproject.toml`, `Maintenance.md` with the
  files and globs its recipes name, and `docs/images/` with the images
  the pages show.  `test/test_keybindings.py` does the same for
  `Keybindings.md`, and `test/test_openwith_command.py` for the variables
  on `External_Commands.md`.  A page renamed or moved has to be repointed
  in all three.
- **Rendering a page** is `cmark-gfm -e table <page> > /dev/null`, and
  the relative links are checked by walking `](target)` for every page
  and asking whether the path exists next to it; both found nothing after
  the move, which is what makes them worth re-running after one.
- **Links that name the project** all point at
  <https://github.com/twwn/mcomix>: `pyproject.toml`'s URLs, the about
  dialog's website, the external-commands dialog's help link, the
  AppStream homepage and update contact, the Chocolatey metadata and the
  MSI the package downloads, and the `--msgid-bugs-address` in the
  translation recipe (so the catalogues' headers carry it too).  What
  stays `net.sourceforge.mcomix` is the AppStream component id, the
  developer id and the Flatpak application id: they identify the
  installed application, and renaming one installs a second application
  beside the first.
