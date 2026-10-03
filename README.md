# mcomix-loop

**An unattended maintenance loop for the [MComix GTK 4 fork](https://github.com/twwn/mcomix), packaged as a [Claude Code](https://code.claude.com/docs) skill.**

You start it once, with `/loop /mcomix-loop`. It wakes every minute. Each time, it picks the most valuable lead it can finish and verify: a bug, a measured slowdown, an incomplete feature, a refactor with a mechanical proof. It commits the work, writes itself notes and schedules the next wakeup. It stops on its own only for a decision that is yours.

It targets the fork's GTK 4 code base, the 4.x line. Upstream MComix 3 is GTK 3. The loop refuses to run there.

## What it does to your machine

Read this before you install it. The loop runs unattended.

- **Commits** – to the checkout `claude` was started in, on whatever branch is checked out. Only after the full test suite, flake8 and mypy pass.
- **Never** – pushes, stashes, stages a file it did not name, or rewrites history.
- **One exception** – the message of its own newest commit, while no remote branch contains it. It uses `git commit --amend --only`, so the tree stays as it is. Any other wrong message gets a `git notes` note.
- **Enforced** – a hook, `scripts/guard.sh`, refuses the forbidden commands. It acts only in the loop's session. Your other Claude Code sessions in the same checkout are unaffected.
- **Runs** – the test suite under `xvfb-run`, and probes it writes itself. Each one in the foreground, inside `timeout`.
- **Writes** – to two places only: the checkout, and `state/` in the skill's directory.
- **Remembers** – in `state/`, an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format) bundle. It holds techniques, your rulings, what it examined and left alone, its notes, probes and gate logs. It records your rulings and never edits them.
- **Keeps out of your MComix data** – `~/.config/mcomix` and `~/.local/share/mcomix`. The hook refuses both. With the settings snippet merged, Claude Code denies them too.
- **Uses `auto` permission mode** – a permission prompt would stall a loop nobody watches. Claude Code's classifier still reviews every command.
- **May open a git worktree** – at `<checkout>/.claude/worktrees/campaign`, for a change too large for one commit. Only for a campaign you approved.

If that is more than you want an unattended process to do, do not install it.

## Requirements

- Linux.
- Claude Code 2.1 or later, with `/loop` and `ScheduleWakeup`, on a plan that offers `auto` mode.
- In the checkout's environment: `pytest` with `pytest-xdist`, `flake8`, `mypy`, `xvfb-run` (from Xvfb) and the gettext tools.
- `jq`, optional. Without it, the hooks read their input with `python3`, which is slower to start.
- A GTK 4 MComix checkout: `mcomix/`, `test/` and `mcomix/constants.py` under a git top level. The hooks, `state.sh` and `gates.sh` check for these.
- `gi.require_version('Gtk', '4.0')` somewhere under `mcomix/`. `state.sh` checks for it.

## Install

As a personal skill, available in every session, with its state outside any repository:

```bash
git clone https://github.com/twwn/mcomix-loop ~/.claude/skills/mcomix-loop
```

Or as a project skill inside the checkout. Then `.claude/` must be in `.git/info/exclude` (step 3):

```bash
git clone https://github.com/twwn/mcomix-loop <checkout>/.claude/skills/mcomix-loop
```

The hooks look in both places. `git pull` updates the skill. `state/` is gitignored, so an update leaves it alone.

Then:

1. **Seed the state.** In the skill's directory: `mkdir -p state && cp -r base/. state/`.

   `base/` is another installation's knowledge of this code base:

   - `techniques/` – how to measure and test it. The valuable part.
   - `rejected.md` – what was examined and found fine.
   - `probes/` – the scripts the techniques name.
   - `notes.md` – cut down to the gate numbers and the leads.

   Three parts describe one installation. Adapt them:

   - `config.sh` – set `WORKERS` to what you measure. `-n auto` is slower on this suite. On Python 3.12 or 3.13, set `EXPORT_DIR` to a short path.
   - `project.md` – replace the author's facts with yours: where your fork stands, how you release, which campaigns are finished.
   - `decisions/` – the author's rulings, one file each. Keep those tagged `program` if you build on this fork; they say why the program behaves as it does. Delete those tagged `installation`. Then confirm the ones you keep: `python3 scripts/okf.py confirm --as <you> state/decisions/*.md`.

   The loop never edits `config.sh`, `project.md` or a ruling. It records new rulings itself. Its prompt marks them unconfirmed until you confirm them. Its first iteration measures the gates on your tree and rewrites the notes as its own.

2. **Merge `settings-snippet.json`** into `~/.claude/settings.json`.

   - `defaultMode: auto` – the loop's permission mode.
   - `additionalDirectories` – needed only for the personal install. Write the absolute path if `~` is not expanded.
   - `deny` – MComix's real data.
   - `BASH_DEFAULT_TIMEOUT_MS` – the full gates take longer than the Bash tool's two-minute default.
   - `attribution.commit` – the commit trailer. Empty, so the loop's commits carry none. Yours to change.
   - `worktree.baseRef: head` – keeps subagent worktrees off `origin/master`.

3. **Hide `.claude/` in the checkout:** `echo '.claude/' >> .git/info/exclude`. The campaign worktree and Claude Code's subagent worktrees live there. The loop reads an untracked path in `git status` as someone's work in progress.

4. **Turn off auto memory in the checkout:** `{"autoMemoryEnabled": false}` in its `.claude/settings.local.json`. Auto memory is a second, uncurated memory. Its index loads into every session. Left on, it collects rulings that belong in `decisions/`, and stale entries there contradict the curated files. The guard refuses the loop's writes there anyway; the setting spares the refused attempts. It applies to every session in that checkout, interactive ones too.

## Run

```text
cd <checkout> && claude
/loop /mcomix-loop                 # or: /loop /mcomix-loop do the three leads
```

At the first wakeup:

- `/hooks` lists three session hooks.
- The first tool call is `state.sh`. Its first line names your checkout.
- `/permissions` → Recently denied is empty.

At the second wakeup, `/context` shows the skill once, not twice.

- `Esc` while the loop waits cancels the pending wakeup.
- Claude Code ends every loop after seven days. Restart it with the same command.
- A loop that stopped by itself says why: in its last report, and in `state/notes.md` under `Questions for the user`.

## How it works

- **`SKILL.md`** – the protocol. Its body is static, so it costs its tokens once per session and once after each compaction.
- **`scripts/state.sh`** – the first command of every iteration. It prints the checkout and its branch, the tree, the commits since the notes' baseline, the notes and the names of the techniques.
- **`scripts/gates.sh`** – runs the suite, then flake8 beside mypy, each with a hard timeout. It prints one line per gate.
- **Exported trees** – `gates.sh --export` measures a clean `git archive`. Exports share one mypy cache, so mypy takes a second there, not half a minute.
- **`guard.sh`** – PreToolUse hook. It enforces the never-rules. It notes each commit the loop makes, to know its own later.
- **`stop-check.sh`** – Stop hook. It keeps a turn going while the gates ran after the notes were last written, or while the bundle is broken. It counts only its own session's gate runs. It never holds back a session outside a checkout.
- **Compaction hook** – SessionStart, on compaction. It prints `invariants.md`.
- **Hooks are per session** – all three are registered only for the session that invoked the skill.
- **Hands off the skill** – the loop edits nothing in this directory except `state/`. Inside `state/` it never edits `config.sh` or `project.md`. The guard enforces both.

### The memory

`state/` is an [OKF 0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format) bundle. Every `.md` in it opens with YAML frontmatter naming its `type`. The `index.md` files are generated. `scripts/okf.py` lists, renders and checks the bundle.

| In `state/` | Type | Holds | Written | Read |
|---|---|---|---|---|
| `notes.md` | Iteration Notes | Gate numbers, open campaign, questions, the last claim, leads | Rewritten every iteration | In full, every iteration |
| `techniques/*.md` | Technique | How to measure and test this code base. One topic each, with the source files it depends on | Added to, corrected in place, never deleted | Names every iteration, flagged when a source changed. Files on demand |
| `rejected.md` | Rejection Register | What was examined and left alone, and why | Added to, corrected in place | By `grep`, before each lead |
| `decisions/*.md` | Ruling | Your rulings in your words, tagged `program` or `installation` | By `okf.py ruling`, never edited. Confirmed by you | One line each, in the prompt. Unconfirmed ones marked |
| `project.md` | Installation | The facts of your installation | By you | In full, in the prompt |

`reference.md` holds the task list and the facts of the code base. It goes into the prompt with the last two.

A technique names its sources as `repo:<path>`, a file in the MComix checkout.

### Commit messages

The guard notes the parent and subject of each commit the loop makes, in `state/commits.log`, before the commit runs. That is how the loop tells its own commits from yours. A commit whose message the guard cannot read in advance is refused.

A wrong message on a commit the loop cannot amend becomes a note. `git log` shows notes. GitHub does not. To carry notes across your own rebases: `git config notes.rewriteRef refs/notes/commits`. Or fold them into the messages.

## Publishing your state

The techniques and the probes improve with use. They are meant to be pushed back.

Run `scripts/publish-base.sh` by hand, with no loop session open. It copies `state/` into `base/`:

- **Whole** – techniques, probes and `rejected.md`. Also the rulings and `project.md`, as the author's worked example.
- **Trimmed** – `notes.md`. The sections about one installation are blanked. The gate numbers are marked as a seed.
- **Never** – `config.sh`, `commits.log` and `scratch/`.

It replaces your home path in what it copies. It regenerates the index files, adds a `log.md` entry and checks conformance. Last, it lists lines that look personal: a home path, a GPU name, another session's review process. Reword or drop them before you commit.

## Adapting it to another project

It is not generic. The project-specific parts are in known places:

- The fingerprint and the settings: `scripts/paths.sh`.
- The gate commands: `scripts/gates.sh`.
- The "Guardrails", "Verification gates" and "Evidence standards" sections of `SKILL.md`. They are about GTK, xdist and MComix's data paths.
- `reference.md`.

The protocol carries over unchanged: state, gates, notes, campaigns, ending, hooks.

## License

[MIT](LICENSE).
