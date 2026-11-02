# mcomix-loop

**An unattended maintenance loop for the [MComix GTK 4 fork](https://github.com/twwn/mcomix), packaged as a [Claude Code](https://code.claude.com/docs) skill.**

You start it once, with `/loop /mcomix-loop`.
It wakes every minute; when all that is left waits on a CI run, after up to fifteen.
Each time, it takes as many leads as it can finish and verify: a bug, a measured slowdown, an incomplete feature, a refactor with a mechanical proof.
It commits each one, writes itself notes and schedules the next wakeup.

It stops by itself for three reasons only:

- **Quiet** – three iterations in a row committed nothing and advanced no campaign.
- **Stuck** – a gate broke, and it can neither fix nor attribute the cause.
- **Your call** – a decision that is yours is all that is left. Until then the question waits in its notes, and it works the other leads.

It targets the fork's GTK 4 code base.
Upstream MComix 3 is GTK 3; the loop refuses to run there.

## What it does to your machine

Read this before you install it.
The loop runs unattended.

- **Commits** – to the checkout `claude` was started in, on whatever branch is checked out. Only after the test suite, flake8 and mypy pass.
- **Never** – pushes, stashes, stages a file it did not name, or rewrites history.
- **One exception** – the message of its own newest commit, while no remote branch contains it. It uses `git commit --amend --only`, so the tree stays as it is. Any other wrong message gets a `git notes` note.
- **Enforced** – a hook, `scripts/guard.sh`, refuses the forbidden commands. It acts only in the loop's session and, with the settings snippet merged, in that session's subagents. Your other Claude Code sessions in the same checkout are unaffected. If the hook itself fails (missing, crashed, timed out), it refuses every command, and the loop stops.
- **Runs** – the test suite under `xvfb-run`, and probes it writes itself. Each in the foreground, inside `timeout`.
- **Writes** – to two places only: the checkout, and `state/` in the skill's directory.
- **Posts to GitHub** – only what `config.sh` names. With `ISSUES_REPO`: issues and comments in that repository, and it closes the ones its commits finished. With `ISSUES_PROJECT`: that project's items and fields. What it posts is public, under your account. Unset, it writes nothing to GitHub.
- **Remembers** – in `state/`, an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format) bundle: techniques, your rulings, what it examined and left alone, its notes, probes and gate logs. It records your rulings and never edits them.
- **Keeps out of your MComix data** – `~/.config/mcomix` and `~/.local/share/mcomix`. The hook refuses both. With the settings snippet merged, Claude Code denies them too.
- **Uses `auto` permission mode** – a permission prompt would stall a loop nobody watches. Claude Code's classifier still reviews every command but one: closing an issue in your repository, which the settings snippet allows.
- **May open a git worktree** – at `<checkout>/.claude/worktrees/campaign`, for a change too large for one commit. Only for a campaign you approved.

If that is more than you want an unattended process to do, do not install it.

## Requirements

- Linux.
- Claude Code 2.1.295 or later, with `/loop` and `ScheduleWakeup`, on a plan that offers `auto` mode. Older versions ignore the guard's `onFailure: block`, so a guard that fails lets the command through.
- In the checkout's environment: `pytest` with `pytest-xdist`, `flake8`, `mypy`, `xvfb-run` (from Xvfb) and the gettext tools.
- `jq`, optional. Without it, the hooks read their input with `python3`, which is slower to start.
- Optional: the tools the techniques name, such as `vulture` and `zizmor`. Install them on the system. `auto` mode refuses to fetch a tool at run time (`uvx vulture`), so the loop asks for a missing one in its notes.
- A GTK 4 MComix checkout: `mcomix/`, `test/` and `mcomix/constants.py` under a git top level. The hooks, `state.sh` and `gates.sh` check for these.
- `gi.require_version('Gtk', '4.0')` somewhere under `mcomix/`. `state.sh` checks for it.

## Install

As a personal skill, available in every session, with its state outside any repository:

```bash
git clone https://github.com/twwn/mcomix-loop ~/.claude/skills/mcomix-loop
```

Or as a project skill inside the checkout, with `.claude/` in `.git/info/exclude` (step 3):

```bash
git clone https://github.com/twwn/mcomix-loop <checkout>/.claude/skills/mcomix-loop
```

The hooks look in both places.
`git pull` updates the skill.
`state/` is gitignored, so an update leaves it alone.

Then:

1. **Seed the state.** In the skill's directory: `mkdir -p state && cp -r base/. state/`.

   `base/` is another installation's knowledge of this code base:

   - `techniques/` – how to measure and test it. The valuable part.
   - `rejected.md` – what was examined and found fine.
   - `probes/` – the scripts the techniques name.
   - `notes.md` – cut down to the gate numbers and the leads.

   Three parts describe one installation. Adapt them:

   - `config.sh` – set `WORKERS` to what you measure; `-n auto` is slower on this suite. On Python 3.12 or 3.13, set `EXPORT_DIR` to a short path. To let the loop file, update and close issues, set `ISSUES_REPO` (`owner/name`) and `ISSUES_PROJECT` (`owner/number`); project items need `gh auth refresh -s project`.
   - `project.md` – replace the author's facts with yours: where your fork stands, how you release, which campaigns are finished.
   - `decisions/` – the author's rulings, one file each. Keep those tagged `program` if you build on this fork: they say why the program behaves as it does. Delete those tagged `installation`. Confirm the ones you keep: `python3 scripts/okf.py confirm --as <you> state/decisions/*.md`.

   The loop never edits `config.sh`, `project.md` or a ruling.
   It records new rulings itself, marked unconfirmed until you confirm them.
   Its first iteration measures the gates on your tree and rewrites the notes as its own.

2. **Merge `settings-snippet.json`** into `~/.claude/settings.json`.

   - `defaultMode: auto` – the loop's permission mode.
   - `additionalDirectories` – needed only for the personal install. Write the absolute path if `~` is not expanded.
   - `allow` – `gh issue close` on the repository `ISSUES_REPO` names, so that closing an issue does not wait on the classifier. Replace `twwn/mcomix` with yours, or drop the rule if `ISSUES_REPO` stays unset. The guard still checks the command first.
   - `deny` – MComix's real data.
   - `BASH_DEFAULT_TIMEOUT_MS` – the full gates take longer than the Bash tool's two-minute default.
   - `attribution.commit` – the commit trailer. Empty, so the loop's commits carry none. Yours to change.
   - `worktree.baseRef: head` – keeps subagent worktrees off `origin/master`.
   - `hooks.PreToolUse` – the guard for the loop's subagents. A skill's own hooks do not fire inside a subagent, so without this one they run unguarded, and `state.sh` says so. It runs on every Bash, Monitor, Write and Edit call of every session. Outside the loop's subagents it exits at once, after a few milliseconds, and it does nothing if the skill is not installed.

3. **Hide `.claude/` in the checkout:** `echo '.claude/' >> .git/info/exclude`. The campaign worktree and Claude Code's subagent worktrees live there. The loop reads an untracked path in `git status` as someone's work in progress.

4. **Turn off auto memory in the checkout:** `{"autoMemoryEnabled": false}` in its `.claude/settings.local.json`.

   Auto memory is a second, uncurated memory, and its index loads into every session.
   Left on, it collects rulings that belong in `decisions/`, and its stale entries contradict the curated files.
   The guard refuses the loop's writes there anyway; the setting spares the refused attempts.
   It applies to every session in that checkout, interactive ones too.

## Run

```text
cd <checkout> && claude
/loop /mcomix-loop                 # or: /loop /mcomix-loop do the three leads
```

At the first wakeup:

- `/hooks` lists three session hooks, and the subagent hook from your settings.
- The first tool call is `state.sh`. Its first line names your checkout.
- `/permissions` → Recently denied is empty.

At the second wakeup, `/context` shows the skill once, not twice.

- **Cancel** – `Esc` while the loop waits cancels the pending wakeup.
- **Seven days** – Claude Code ends every loop after seven days. Restart it with the same command.
- **Why it stopped** – in its last report, and in `state/notes.md` under `Questions for the user`.

## How it works

- **`SKILL.md`** – the protocol. Its body is static, so it costs its tokens once per session and once after each compaction.
- **`scripts/state.sh`** – the first command of every iteration. It prints the checkout and its branch, the tree, the commits since the notes' baseline, the issues and discussions on GitHub, the notes and the names of the techniques.
- **`scripts/gates.sh`** – runs the suite, then flake8 beside mypy, each with a hard timeout. It prints one line per gate.
- **Exported trees** – `gates.sh --export` measures a clean `git archive`. Exports share one mypy cache, so mypy takes a second there, not half a minute.
- **Worktrees** – `gates.sh --tree` keeps the logs of a tree other than the checkout in `state/scratch/logs/<tree>/`, so gates can run at once in two worktrees. Exports cannot: each new one removes the last.
- **`guard.sh`** – PreToolUse hook. It enforces the never-rules. It notes each commit the loop makes, to know its own later.
- **`subagent-guard.sh`** – PreToolUse hook from your settings. It runs `guard.sh` for the subagents of a loop session, which it knows by the mark `guard.sh` leaves in `state/scratch/sessions/`. In any other session it does nothing.
- **`stop-check.sh`** – Stop hook. It keeps a turn going while the gates ran after the notes were last written, or while the bundle is broken. It counts only its own session's gate runs. It never holds back a session outside a checkout.
- **Compaction hook** – SessionStart, on compaction. It prints `invariants.md`.
- **Hooks are per session** – the three in `SKILL.md` are registered only for the session that invoked the skill.
- **Hands off the skill** – the loop edits nothing in this directory except `state/`. Inside `state/` it never edits `config.sh` or `project.md`. The guard enforces both.

### The memory

`state/` is an [OKF 0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format) bundle.
Every `.md` in it opens with YAML frontmatter naming its `type`.
The `index.md` files are generated.
`scripts/okf.py` lists, renders and checks the bundle.

| In `state/` | Type | Holds | Written | Read |
|---|---|---|---|---|
| `notes.md` | Iteration Notes | Gate numbers, open campaign, questions, the last claim, leads | Rewritten every iteration | In full, every iteration |
| `techniques/*.md` | Technique | How to measure and test this code base. One topic each, with the source files it depends on | Added to, corrected in place with Edit, never deleted | Names every iteration, flagged when a source changed. Files on demand |
| `rejected.md` | Rejection Register | What was examined and left alone, and why | Added to, corrected in place with Edit | By `grep`, before each lead |
| `decisions/*.md` | Ruling | Your rulings in your words, tagged `program` or `installation` | By `okf.py ruling`, never edited. Confirmed by you | One line each, in the prompt. Unconfirmed ones marked |
| `project.md` | Installation | The facts of your installation | By you | In full, in the prompt |

`reference.md` holds the task list and the facts of the code base.
It goes into the prompt with the last two.

A technique names its sources as `repo:<path>`, a file in the MComix checkout.

### Commit messages

The guard notes the parent and subject of each commit the loop makes, in `state/commits.log`, before the commit runs.
That is how the loop tells its own commits from yours.
A commit whose message the guard cannot read in advance is refused.

A wrong message on a commit the loop cannot amend becomes a note.
`git log` shows notes; GitHub does not.
To carry notes across your own rebases: `git config notes.rewriteRef refs/notes/commits`.
Or fold them into the messages.

## Publishing your state

The techniques and the probes improve with use.
They are meant to be pushed back.

Run `scripts/publish-base.sh` by hand, with no loop session open.
It copies `state/` into `base/`:

- **Whole** – techniques, probes and `rejected.md`. Also the rulings and `project.md`, as the author's worked example.
- **Trimmed** – `notes.md`. The sections about one installation are blanked. The gate numbers are marked as a seed.
- **Never** – `config.sh`, `commits.log` and `scratch/`.

It replaces your home path in what it copies.
It regenerates the index files, adds a `log.md` entry and checks conformance.
Last, it lists lines that look personal: a home path, a GPU name, another session's review process.
Reword or drop them before you commit.

## Adapting it to another project

It is not generic.
The project-specific parts are in known places:

- **Fingerprint and settings** – `scripts/paths.sh`.
- **Gate commands** – `scripts/gates.sh`.
- **The GTK, xdist and data-path rules** – the "Guardrails", "Verification gates" and "Evidence standards" sections of `SKILL.md`.
- **The code base's facts** – `reference.md`.

The protocol carries over unchanged: state, gates, notes, campaigns, ending, hooks.

## License

[MIT](LICENSE).
