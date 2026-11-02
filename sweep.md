# MComix loop: sweeps

When no lead can be worked, the loop looks for more before it counts itself
quiet: auditors, one lens each, each in a worktree of its own, look for what
the notes and `REJECTED` do not hold yet. They change nothing; the main thread
checks what they report and keeps what survives. Read this file when
`state.sh` lists lenses as due and the pick has come to a sweep. Do not edit it
(the guard refuses); `sweep.sh` takes the auditors' brief and the lenses from
here.

## The main thread

1. Run `${CLAUDE_SKILL_DIR}/scripts/sweep.sh start`, which takes the lenses due
   (or those named after `start`) at the configured tier. It writes a brief for
   each and prints one line per lens: `<lens> <model> <effort>: <prompt>`. Append
   "sweep open: read sweep.md" to `SCRATCH/iteration.txt`.

   To give a lens another tier, name every lens that is due, the tier on those
   that differ: `sweep.sh start twins docs=sonnet/medium outside=opus/high`.
   Each lens's last run is in `STATE/sweeps.log`: time, lens, commit, returned,
   survived, model, effort. Name a tier only for one of these reasons:
   - **Up to `opus/high`:** in its last run at this tier, most of the lens's
     leads did not survive. A checked false lead costs the main thread more than
     the auditor saves.
   - **Down to `sonnet/medium`:** `docs` or `twins`, whose work is comparing
     lists, if every lead of the last run survived.
2. One `Agent` call per line, all in one message: `subagent_type`
   `general-purpose`, `isolation` `worktree`, `description` `Sweep: <lens>`,
   `model` and `effort` as printed, `prompt` as printed, with nothing added. The
   calls return at once.
3. Run `sweep.sh wait` again and again, in the foreground, until it says that
   all are in or that the deadline has passed. While it says to wait, do not end
   the turn and do nothing else. An auditor's notification says nothing its
   report does not, and changes nothing here: go back to `wait`.
4. Read the reports, `SCRATCH/sweep/<lens>.md`, and check each lead as step 5 of
   "Start of every iteration" does: `grep -n` its place in `REJECTED`, then run
   its command yourself, from `REPO`, at HEAD. A probe under `SCRATCH/sweep/`
   takes `PYTHONPATH=<REPO>`. An auditor's probe is a claim: prove the probe
   before you believe it. A lead marked `unproven` survives only if you can
   follow its chain from the code yourself.
5. What survives goes under `Leads worth picking up`, ranked with what is there
   and with its evidence as you saw it. What would change what MComix is goes
   under `Questions for the user`. What does not survive goes to `REJECTED` as
   you find it, saying what you saw, so that no later sweep reports it again.
   A probe that proved itself goes to `STATE/probes`, with a technique. When the
   survivors would push the notes past their cap, the rest wait in
   `SCRATCH/sweep-backlog.md`, which the notes name.
6. `sweep.sh done <lens> <returned> <survived>` for each lens, with `-` and `-`
   for one that never reported. The last one closes the sweep. A lens that left
   no lead rests until `SWEEP_EVERY` commits have touched `mcomix/` or `docs/`;
   the others are due again when the leads next run out.
7. Go on with the iteration: a lead can be worked now, so work it. A sweep
   that left no lead is a quiet iteration like any other.

## The auditor

You are an auditor in a sweep of MComix, a GTK4/PyGObject comic book viewer. An
unattended loop maintains it and has run out of work. You look through one lens
for what it has not found. You change nothing: the main thread checks what you
report and decides what becomes work. A report of no leads is a good result. A
padded one costs the loop more than it gains.

Your working directory is a worktree of commit {COMMIT}, used by nothing else.
Check with `git rev-parse --short HEAD`; if it prints another commit, say so in
the first line of your report. Read and run there. It is removed when you finish,
so nothing you report may name its path. `cd` does not carry from one Bash call
to the next, and the shell is zsh.

1. **Know what is known.** The leads and questions below are known already.
   `{REJECTED}` holds what was examined and left alone, one line each beginning
   with where: `grep -n` it for a file or function before you spend time there,
   and never read it whole. An entry is not reopened without evidence it did not
   have. The rulings below are the user's, and what they decide is not a bug.
   `{TECHNIQUES}` holds how to test this code base, one file per topic: read the
   ones your lens names, and `ls` it for one on whatever you are about to probe.
   Before your first probe read `probes.md` and `building-the-book-a-test-needs.md`
   there; they may name a ready probe under `{PROBES_READY}`.
2. **Look**, through your lens and nowhere else. Prefer what a user meets at
   ordinary speed on an ordinary book over what takes a contrived sequence.
   Search mechanically where you can (`git grep`, an `ast` walk), then read what
   it finds; the technique `sweeps-that-found-work.md` shows the shape. Taste is
   not a lead. Nor is speed: auditors run side by side, so no timing taken here
   means anything.
3. **Show it.** For each candidate, the smallest command that shows it happen: a
   probe built on `test/__init__.py:MComixTest`, kept under `{PROBES}` and run
   with `PYTHONPATH=$PWD`, or a test of the suite run with a changed input. Every
   script goes under `{PROBES}`, a throwaway one too, and none under `/tmp`: the
   main thread runs your command again from another tree, so it has to work from
   any checkout. Then try to prove yourself wrong: a probe that surprises you is
   wrong until shown otherwise. What timing will not let you show (a race) may be
   reported by its chain of file:line, marked `unproven`; it ranks below what you
   showed.
   Everything runs in the foreground inside `timeout -k 5 <seconds>`. A subset of
   the suite, never all of it:
   `env -u WAYLAND_DISPLAY GDK_BACKEND=x11 timeout -k 5 60 xvfb-run -d -s "-screen 0 1280x1024x24" python3 -m pytest test/<file> -q -n 2`
4. **Stop** at five leads or about sixty tool calls, whichever comes first.
5. **Report**, once, as your last action, with the Write tool, to `{REPORT}`, in
   this form and nothing else:

       # {LENS} at <commit>
       - <file>:<line> - <what goes wrong, in a user's terms>. Evidence: `<command>` printed `<the line that shows it>`. Size: Small|Medium|Large.

   Strongest first, one line each; add the `REJECTED` line a lead reopens and
   what is new, if it does; put `unproven` after `Evidence:` where it applies.
   With nothing to report, the one line `No leads.` under the heading. Your final
   message is one line: `{LENS}: <n> leads`.

The guard refuses what an auditor has no use for: writing outside `{PROBES}` and
your report, any git command that is not a read, anything sent to GitHub. A
refusal is not a puzzle to route around. Write nothing in your worktree.

## The lenses

The first run takes them in this order. Nothing here is a claim that such a bug
exists.

### twins

A behaviour offered in one place and missing or different in its twin, where a
user would expect both: the reader and the library (cover menu, keys, what a
selection means), the menu entry, tool bar button and key for one action, one
page and two, manga order and not, a folder book and an archive, each archive
format, two dialogs that show one setting. Options defined and never read;
actions nothing can reach. Compare the two lists mechanically where you can. A
difference a ruling decides is no lead, and one that would change what MComix is
says so.

Read first: `actions-nothing-can-reach-menus-tool-bar-keys.md`, `changing-the-pages-of-the-open-book.md`, `adding-a-keyboard-action.md`, `private-names-and-dead-code-ast-sweeps.md`.

### outside

What comes from outside the program and is not what the code assumes, seen from
where the reader sits: names and text from other systems, a damaged or odd
archive or image, a file system that refuses (read-only, full, the file gone or
replaced meanwhile). An operation the user asked for and is watching that fails
with a log line and nothing on screen. Anything lost because a step after the
point of no return failed. The fuzz targets cover the parsers' crashes, so look
at what the reader gets, not at whether they crash.

Read first: `names-and-text-from-other-systems-zip-names.md`, `file-uris-and-content-types-glib-s-never-urllib.md`, `encrypted-archives-nothing-asks-on-the-reader-s.md`, `text-a-reader-typed-used-as-a-pattern.md`, `forward-compatible-stores-what-an-older-mcomix.md`.

### threads

What a worker thread and the main loop share, and what is checked and then acted
on after it may have changed: results delivered to a page, book or window that
has since changed, a flag read without the lock that writes it, an `idle_add`
callback that assumes the state it was queued under. Turning pages fast and
closing a book while thumbnails load are ordinary speed; a race only a debugger
could produce is not.

Read first: `threads-that-share-one-thing.md`, `which-thread-reaches-something-across-the-whole.md`, `check-then-act-on-the-file-system-and-code.md`, `a-worker-that-aborts-inside-gtk.md`, `flakes-make-the-rare-case-common.md`.

### lifetime

State that outlives what owns it: signal handlers, `GLib.timeout_add` and
`idle_add` sources, listeners on long-lived objects, dialogs and popovers that
fire or stay after their window, book or library entry has gone. What does each
long-lived object still hold after a book is closed, or a second window is opened
and closed? What happens when the book moves, or goes, while it is open?

Read first: `listeners-that-outlive-what-they-belong-to.md`, `dialogs-and-widgets-that-outlive-their-window.md`, `gtk-reference-counts-from-python.md`, `every-way-a-book-is-left-and-the-question-about.md`, `what-follows-a-book-that-moves-or-goes.md`.

### port

What the move from GTK 3 to GTK 4 left subtly wrong: a handler run again by what
it sets itself (`set_active()` from code emits `toggled`; `close()` emits
`close-request` before it returns); a page number counted from one used where an
index counted from zero is meant, or the reverse; an event controller on the
wrong widget or in the wrong phase; what works by key and not by pointer; focus,
selection and mnemonics. Real events under Xvfb show what a call does not.

Read first: `checking-what-the-port-changed.md`, `pygobject-introspection-traps.md`, `a-real-click-drag-or-key-under-xvfb-xdotool.md`, `a-click-into-an-unfocused-window-focus-first.md`, `a-gtk-entry-in-a-dialog-selects-all-of-itself.md`.

### docs

What `docs/` and `README.md` tell the reader that the program does not do: every
key, option, menu entry, file format, path and limit they name, checked against
the code or by running it. `test_wiki.py`, `test_keybindings.py` and
`test_openwith_command.py` catch some of it, so read them first and look at what
they do not. Wrong and missing, not style: the brevity ruling applies to any
wording you propose.

Read first: `documentation-where-it-lives-and-what-checks-it.md`.

### windows

What holds on Linux and not on Windows, in code that runs there: an open file
cannot be moved or replaced, drive letters and separators, names that differ only
by case, a console window per subprocess, branches on the platform that no test
here runs. Under Wine a probe is slow, so a chain of file:line that names the call
and what Windows does with it may stand as `unproven`.

Read first: `windows-what-the-tests-must-not-assume.md`, `windows-refuses-to-move-or-replace-an-open-file.md`, `the-windows-branches-of-portability-py-run-on.md`, `the-test-suite-under-wine.md`.
