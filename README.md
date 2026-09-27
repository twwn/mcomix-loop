# mcomix-loop

A self-scheduling maintenance loop for the [MComix GTK4 fork](https://github.com/twwn/mcomix),
packaged as a [Claude Code](https://code.claude.com/docs) skill. Started once
with `/loop /mcomix-loop`, it wakes every minute, picks the most valuable lead it can
finish and verify — a bug, a measured slowdown, an incomplete feature, a refactor with a
mechanical proof — commits it, hands itself notes, and reschedules. It stops on its own
only for a decision that is yours.

It targets that fork's GTK4 code base (the 4.x line). Upstream MComix 3.x is GTK3, and
the loop refuses to run there.

## What it does to your machine

Read this before installing; the loop runs unattended.

- It commits to the checkout `claude` was started in, on whatever branch is checked out,
  after the full test suite, flake8 and mypy pass. It never pushes, never stashes, never
  stages files it did not name, and never rewrites history, with one exception: the
  message of its own newest commit while no remote branch contains it (`--amend --only`,
  the tree unchanged). Any other wrong message gets a `git notes` note instead. Those are
  not habits: a hook (`scripts/guard.sh`) refuses the commands, session-scoped, so your
  other Claude Code sessions in the same checkout are unaffected, and notes the parent and
  subject of each commit the loop makes, which is how it knows the loop's own.
- It runs the suite under `xvfb-run` and probes it writes itself, every one wrapped in
  `timeout`, in the foreground.
- It writes only two places: the checkout, and `state/` inside this directory, its
  memory: an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format)
  bundle of techniques, your rulings (which it records but never edits), what it examined
  and left alone, its notes, the probes the techniques name, and gate logs. The real
  MComix configuration under `~/.config/mcomix` and `~/.local/share/mcomix` is refused
  by the hook and, if you merge the settings snippet, denied by Claude Code itself.
- It runs in `auto` permission mode, because a permission prompt stalls a loop nobody
  is watching. Claude Code's own classifier still reviews every command.
- It may open a git worktree at `<checkout>/.claude/worktrees/campaign` for a change
  too large for one commit, and only when you have said yes to that campaign.

If any of that is more than you want an unattended process to do, do not install it.

## Requirements

- Claude Code with `/loop` and `ScheduleWakeup` (2.1.x or later), a plan on which
  `auto` mode is available, Linux.
- In the checkout's environment: `pytest` with `pytest-xdist`, `flake8`, `mypy`,
  `xvfb-run` (from Xvfb), the gettext tools for translations. `jq` is optional (the
  hooks fall back to `python3`).
- A GTK4 MComix checkout: `mcomix/`, `test/`, `mcomix/constants.py` under a git top
  level, with `gi.require_version('Gtk', '4.0')` somewhere under `mcomix/`. That
  fingerprint is checked by every script and by the hook.

## Install

As a personal skill (available in every session, the state kept out of any repository):

    git clone https://github.com/twwn/mcomix-loop ~/.claude/skills/mcomix-loop
    chmod +x ~/.claude/skills/mcomix-loop/scripts/*.sh ~/.claude/skills/mcomix-loop/scripts/okf.py

or as a project skill inside the checkout (`.claude/` must then be in `.git/info/exclude`,
see below):

    git clone https://github.com/twwn/mcomix-loop <checkout>/.claude/skills/mcomix-loop

The hooks in `SKILL.md` look in both places. `git pull` updates the skill; `state/` is
gitignored and untouched.

Then:

1. Seed the state: `mkdir -p state && cp -r base/. state/`. `base/` holds another
   installation's knowledge of this code base: `techniques/` (how to measure and test it;
   the valuable part), `rejected.md` (what was examined and found fine), the `probes/`
   the techniques name, and `notes.md` cut down to gate numbers. Three things in it are
   about one installation and yours to adapt:
   - `config.sh`: set `WORKERS` to what you measure (`-n auto` is slower on this suite);
     on Python 3.12 or 3.13 set `EXPORT_DIR` to a short path.
   - `project.md`: replace the author's facts with yours (where your fork stands, how you
     release, campaigns already finished).
   - `decisions/`: the author's rulings, one file each. Keep those tagged `program` if you
     build on this fork (they say why the program behaves as it does), delete those
     tagged `installation`, then confirm what you keep: `python3 scripts/okf.py confirm
     --as <you> state/decisions/*.md`. The loop records new rulings there itself and
     marks the unconfirmed ones in its prompt until you do the same for them.

   The loop never edits `config.sh`, `project.md` or a ruling. The first iteration
   re-baselines the gate numbers on your tree and rewrites the notes as its own.
2. Merge `settings-snippet.json` into `~/.claude/settings.json`. `additionalDirectories`
   is needed only for the personal-skill install (write the absolute path if `~` is not
   expanded); `attribution.commit` is the commit trailer, yours to change; `worktree.baseRef:
   head` keeps subagent worktrees off `origin/master`; `BASH_DEFAULT_TIMEOUT_MS` because
   the full gates exceed the tool's two-minute default.
3. In the checkout: `echo '.claude/' >> .git/info/exclude`. The campaign worktree and
   Claude Code's own subagent worktrees live under `.claude/`, and the loop reads an
   untracked path in `git status` as someone's work in progress.
4. In the checkout's `.claude/settings.local.json`: `{"autoMemoryEnabled": false}`.
   Claude Code's auto memory is a second, uncurated memory whose index loads into every
   session; left on, the loop files rulings there instead of in `decisions/`, and stale
   entries contradict the curated files. The guard refuses the loop's writes there either
   way; the setting spares it the refused attempts. It applies to every session in that
   checkout, interactive ones included.

## Run

    cd <checkout> && claude
    /loop /mcomix-loop                 # or: /loop /mcomix-loop do the three leads

First wakeup: `/hooks` lists three session hooks; the first tool call is `state.sh` and
its first line names your checkout; `/permissions` → Recently denied is empty. Second
wakeup: `/context` shows the skill once, not appended again. `Esc` while the loop waits
cancels the pending wakeup. Claude Code ends every loop after seven days; restart with
the same command. A loop that stopped by itself says why in its last report and in
`state/notes.md` under `Questions for the user`.

## How it works

`SKILL.md` is the protocol; its body is static, so it costs its tokens once per session
and once after each compaction. The loop never edits anything in this directory except
`state/`, and inside `state/` never `config.sh` or `project.md`; a hook enforces that.
`scripts/state.sh` is the first command of every iteration and prints the checkout and
its branch, the tree, the commits since the notes' baseline, the notes and the names of the
techniques. `scripts/gates.sh` runs the three gates with hard timeouts and prints one line
each. Three hooks are registered for the session that invoked the skill: `guard.sh`
(PreToolUse: the never-rules, and which commits are the loop's), `stop-check.sh` (Stop: no
ending a turn whose gates ran after the notes were written, or while the bundle is broken),
and a SessionStart hook on compaction that prints `invariants.md`.

The memory is an [OKF 0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format)
bundle: every `.md` in `state/` opens with YAML frontmatter naming its `type`, the
`index.md` files are generated, and `scripts/okf.py` lists, renders and checks it (the Stop
hook refuses to end a turn while a concept's frontmatter is broken).

| in `state/` | type | holds | written | read |
|---|---|---|---|---|
| `notes.md` | Iteration Notes | gate numbers, open campaign, questions, the last claim, leads | rewritten every iteration | in full, every iteration |
| `techniques/*.md` | Technique | how to measure and test this code base, one topic each, with the source files it depends on | added to, corrected in place, never deleted | names every iteration (flagged when a source file changed since), files on demand |
| `rejected.md` | Rejection Register | what was examined and left alone, and why | added to, corrected in place | `grep` before a lead |
| `decisions/*.md` | Ruling | your rulings, in your words, `program` or `installation` | created by `okf.py ruling`, never edited; confirmed by you | one line each, injected into the prompt, unconfirmed ones marked |
| `project.md` | Installation | the facts of your installation | by you | in full, injected into the prompt |

`reference.md` holds the task list and the facts of the code base and is injected with the
last two. A technique's sources are written `repo:<path>`, a file in the MComix checkout.

A wrong message on a commit the loop could not amend is a note: `git log` shows it, GitHub
does not, and `git config notes.rewriteRef refs/notes/commits` carries notes across your own
rebases if you would rather keep them than fold them into the messages.

## Publishing your state

The techniques and the probes get better with use and are meant to be pushed back.
`scripts/publish-base.sh`, run by hand with no loop session open, copies `state/` into
`base/`: techniques, rulings, `rejected.md`, `project.md` and probes whole (the rulings and
`project.md` as the author's worked example), `notes.md` with the sections that belong to
one installation blanked and the gate numbers marked as a seed, never `config.sh` or
`commits.log`. It replaces your home path in what it copies, regenerates the index files,
adds a `log.md` entry and checks conformance. It then lists lines that look personal (a
home path, GPU names, a review process another session ran) for you to reword or drop
before committing.

## Adapting it to another project

It is not generic, but the project-specific parts are in known places: the fingerprint
and settings in `scripts/paths.sh`; the gate commands in `scripts/gates.sh`; the
"Guardrails", "Verification gates" and "Evidence standards" sections of `SKILL.md`,
which are about GTK, xdist and MComix's data paths; and `reference.md`. The protocol —
state, gates, notes, campaigns, ending, the hooks — carries over unchanged.

## License

MIT. See `LICENSE`.
