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
  after the full test suite, flake8 and mypy pass. It never pushes, never rewrites
  history, never stashes, never stages files it did not name. Those are not habits: a
  hook (`scripts/guard.sh`) refuses the commands, session-scoped, so your other Claude
  Code sessions in the same checkout are unaffected.
- It runs the suite under `xvfb-run` and probes it writes itself, every one wrapped in
  `timeout`, in the foreground.
- It writes only two places: the checkout, and `state/` inside this directory (its
  notes, a file of techniques that is never pruned, the probes those name, gate logs,
  one export at a time). The real
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
    chmod +x ~/.claude/skills/mcomix-loop/scripts/*.sh

or as a project skill inside the checkout (`.claude/` must then be in `.git/info/exclude`,
see below):

    git clone https://github.com/twwn/mcomix-loop <checkout>/.claude/skills/mcomix-loop

The hooks in `SKILL.md` look in both places. `git pull` updates the skill; `state/` is
gitignored and untouched.

Then:

1. Seed the state: `mkdir -p state && cp -r base/. state/`. `base/` holds another
   installation's knowledge of this code base — `techniques.md` (never pruned, the
   valuable part), the `probes/` it names, `notes.md` cut down to gate numbers, open leads
   and dead ends — plus two files that are yours to edit: `config.sh` (set `WORKERS` to
   what you measure, `-n auto` is slower on this suite; on Python 3.12 or 3.13 set
   `EXPORT_DIR` to a short path) and `project.md` (replace the author's facts with yours:
   where your fork stands, standing decisions, campaigns already finished). The loop reads
   those two and edits neither. The first iteration re-baselines the gate numbers on your
   tree and rewrites the notes as its own; the techniques file it keeps and extends.
2. Merge `settings-snippet.json` into `~/.claude/settings.json`. `additionalDirectories`
   is needed only for the personal-skill install (write the absolute path if `~` is not
   expanded); `attribution.commit` is the commit trailer, yours to change; `worktree.baseRef:
   head` keeps subagent worktrees off `origin/master`; `BASH_DEFAULT_TIMEOUT_MS` because
   the full gates exceed the tool's two-minute default.
3. In the checkout: `echo '.claude/' >> .git/info/exclude`. The campaign worktree and
   Claude Code's own subagent worktrees live under `.claude/`, and the loop reads an
   untracked path in `git status` as someone's work in progress.

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
`state/`, and inside `state/` never `config.sh` or `project.md`; a hook enforces that. `scripts/state.sh` is the first command of every
iteration and prints the tree, the commits since the notes' baseline, the notes and the
headings of the techniques file. `scripts/gates.sh` runs the three gates with hard
timeouts and prints one line each. Three hooks are registered for the session that
invoked the skill: `guard.sh` (PreToolUse, the never-rules), `stop-check.sh` (Stop: a
turn whose gates ran after the notes were last written does not end), and a
SessionStart hook on compaction that prints `invariants.md`. `reference.md` holds the
task list and the facts of the code base; `state/project.md` holds the facts of your
installation; both are injected at the end of the prompt.

The notes file is the loop's memory: about 80 lines, rewritten every iteration, with
gate numbers as of a commit, the open campaign, decisions and questions, what the last
iteration changed with the command that proves each claim, ranked leads with evidence,
and what was checked and rejected. The techniques file is append-only and never pruned.

## Publishing your state

The techniques file and the probes get better with use and are meant to be pushed back.
`scripts/publish-base.sh`, run by hand with no loop session open, copies
`state/techniques.md` and `state/probes/` into `base/`, and copies `state/notes.md` with
the sections that belong to one installation (decisions, questions, the last iteration,
prompt corrections) blanked and the gate numbers marked as a seed. It then lists lines that
look machine- or installation-specific — `/tmp` paths, GPU names, a review process another
session ran — for you to reword or drop before committing. `config.sh` and `project.md`
are not copied; `base/` carries them as examples.

## Adapting it to another project

It is not generic, but the project-specific parts are in known places: the fingerprint
and settings in `scripts/paths.sh`; the gate commands in `scripts/gates.sh`; the
"Guardrails", "Verification gates" and "Evidence standards" sections of `SKILL.md`,
which are about GTK, xdist and MComix's data paths; and `reference.md`. The protocol —
state, gates, notes, campaigns, ending, the hooks — carries over unchanged.

## License

MIT. See `LICENSE`.
