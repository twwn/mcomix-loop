---
name: mcomix-loop
description: One iteration of the unattended MComix maintenance loop, in the MComix checkout claude was started in. Run only through `/loop /mcomix-loop`; never invoke it for another task.
argument-hint: "[request for this iteration]"
effort: high
allowed-tools: Bash(git *) Bash(cat *) Bash(ls *) Bash(grep *) Bash(test *) Bash(mkdir *) Bash(cp *) Bash(mv *) Bash(diff *) Bash(env *) Bash(timeout *) Bash(xvfb-run *) Bash(python3 *) Bash(msgfmt *) Bash(msgmerge *) Bash(xgettext *) Bash(${CLAUDE_SKILL_DIR}/scripts/gates.sh *) Bash(${CLAUDE_SKILL_DIR}/scripts/state.sh *) Read Edit Write Glob Grep Agent WebFetch(domain:docs.python.org)
disallowed-tools: AskUserQuestion EnterPlanMode ExitPlanMode EnterWorktree ExitWorktree
hooks:
  PreToolUse:
    - matcher: "Bash|Monitor|Write|Edit"
      hooks:
        - type: command
          command: 'd=$HOME/.claude/skills/mcomix-loop; [ -d "$d/scripts" ] || d=$CLAUDE_PROJECT_DIR/.claude/skills/mcomix-loop; exec "$d/scripts/guard.sh"'
          timeout: 10
  Stop:
    - hooks:
        - type: command
          command: 'd=$HOME/.claude/skills/mcomix-loop; [ -d "$d/scripts" ] || d=$CLAUDE_PROJECT_DIR/.claude/skills/mcomix-loop; exec "$d/scripts/stop-check.sh"'
          timeout: 10
  SessionStart:
    - matcher: compact
      hooks:
        - type: command
          command: 'd=$HOME/.claude/skills/mcomix-loop; [ -d "$d/scripts" ] || d=$CLAUDE_PROJECT_DIR/.claude/skills/mcomix-loop; cat "$d/invariants.md"'
          timeout: 5
---

# MComix maintenance loop

You are maintaining MComix, a GTK4/PyGObject comic book viewer (about 30,000
lines of Python). The checkout is `REPO`: the directory `claude` was started
in, which is the session's working directory; `state.sh` prints its path
first, and every script refuses to run anywhere that is not an MComix
checkout. One iteration is one invocation of this skill. Its body is static,
so the harness appends it once per session and again, truncated, after each
compaction; the state comes from `state.sh` below. Iterations share one
session that is compacted as it fills, so the conversation is unreliable
memory; what carries across is `git log` and `STATE` = `state/` beside this
file, the one place outside `REPO` the loop writes (`state.sh` prints its
absolute path; use it absolute, since shell variables do not survive from one
command to the next). `STATE` is an Open Knowledge Format bundle: every `.md`
in it opens with YAML frontmatter naming its `type`, `scripts/okf.py` reads and
checks it, and the `index.md` files are generated. Written one line per
paragraph or list entry, never hard-wrapped: an Edit then matches the text
as it is.

- `LOOP_NOTES` = `STATE/notes.md` (`type: Iteration Notes`) — the previous
  iteration's handoff: state, leads, open questions. Capped, rewritten every
  iteration, frontmatter kept.
- `LOOP_TECHNIQUES` = `STATE/techniques/<name>.md`, one `type: Technique`
  concept each: how to measure and test this code base (rules in "Handoff:
  `LOOP_TECHNIQUES`"). `state.sh` lists the names; `[sources changed]`
  after one means a file it depends on changed since it was last written
  or verified - re-check what you rely on before quoting it.
- `DECISIONS` = `STATE/decisions/`, one `type: Ruling` file each: the
  user's rulings in their words, tagged `program` or `installation`,
  injected at the end of this file. Record one the moment it is given, and
  only so: `python3 ${CLAUDE_SKILL_DIR}/scripts/okf.py ruling --tag <tag>
  --title "<short>" --text '"<their words>" - <what it means>'`. Never
  edited: a changed ruling is a new one naming the date it replaces; the
  newest wins. Rulings only (a request once done counts: it stops a later
  iteration "fixing" it back), not events. `(unconfirmed)` marks one the
  user has not confirmed yet (`okf.py confirm` is theirs): follow it, but
  when the tree or the user disagrees with it, ask rather than act on it.
- `REJECTED` = `STATE/rejected.md` (`type: Rejection Register`) — what was
  examined and deliberately left alone, one line each beginning with where
  (`- backend.py:548 - ... Left (f792f346).`), added at the end, never
  pruned; one proven wrong is corrected in place, "(reopened at <commit>:
  ...)". Never read whole: `grep -n` it.
- `STATE/probes/` — probes that proved themselves, under the names the
  techniques give them. One named but missing (`state.sh` lists them) is
  rebuilt from its description when needed; not a prompt correction.
- `SCRATCH` = `STATE/scratch/` — gate logs, exports, `iteration.txt`; what
  one iteration needs, outside the bundle, not preserved.
- `STATE/project.md` (`type: Installation`) and `STATE/config.sh` are the
  user's: the facts of this installation and the loop's settings. Read,
  never edit; a ruling goes to `DECISIONS`, and nothing waits on the user
  folding it in.
- Claude Code's own auto memory (`~/.claude/projects/*/memory/`) is not
  this loop's memory, and the guard refuses writes there.

**This file states rules, not status**: whether a campaign is open, the gate
numbers, the next lead live in `LOOP_NOTES` only, since status written here
goes stale and still reads as current. Do not edit this file or
`reference.md` (the guard refuses); what the tree contradicts in them goes
under `Prompt corrections` in `LOOP_NOTES` for the user.

## State

The first action of every iteration, before any other tool call, is
`${CLAUDE_SKILL_DIR}/scripts/state.sh`. It prints the checkout and the
branch it is on (`BRANCH`, whatever its name), the tree, the commits since
the baseline `LOOP_NOTES` names (foreign unless the notes say otherwise),
worktrees and `loop/*` branches, `LOOP_NOTES` in full (MISSING means a fresh
chain), the names of the `LOOP_TECHNIQUES` concepts (Read the one you
need before writing a probe or benchmark), bundle problems if any, and a
protocol footer. It is not re-run after a compaction: `SCRATCH/iteration.txt`
holds what this iteration has found since.

Request from the user for this iteration (empty on a scheduled wakeup):
$ARGUMENTS

## Ending an iteration

Every iteration ends the same way, whatever it did.

1. Rewrite `LOOP_NOTES` (sections below). Add to `LOOP_TECHNIQUES` whatever
   proved itself and to `REJECTED` whatever was examined and left alone (if
   not done as it happened). Fold in `SCRATCH/iteration.txt` and delete it.
2. Write the report (see Reporting). The turn's final message is the report.
3. **The last action is `ScheduleWakeup`** with `prompt`: the literal string
   `/mcomix-loop`; `delaySeconds`: `60`, the floor, unless the only work
   left waits on a CI run the loop reads itself — then up to `900`, and the
   `reason` names the run; never pad it otherwise; `noop`: `false` if
   anything was committed or a campaign advanced, `true` otherwise;
   `reason`: one line naming what the next iteration should pick up.

   **Stop instead** — `ScheduleWakeup` with `stop: true`, and a
   `PushNotification` naming the reason — for exactly these, and say which:
   - **Three consecutive quiet iterations**, counted by the `Quiet
     iterations` line: increment when nothing was committed, reset when
     something was or a campaign advanced. When the leads run out,
     `DECISIONS` or `project.md` may say what comes next — a release commit,
     a sweep; that is then the lead, and the count starts after it.
   - **A broken gate you can neither fix nor attribute**, recorded in
     `LOOP_NOTES` first.
   - **A decision that is the user's, with nothing else left to do**: a
     floor to raise, a feature to add or drop, a campaign to open — anything
     that changes what MComix is rather than how well it does it. While other
     leads exist, the question waits under `Questions for the user`, dated,
     and the loop works the leads; it stops only when the decision is all
     that stands between it and idleness.

   Do not stop because the obvious work is done, and never with a campaign
   open unless one of the above applies. The harness's seven-day limit and
   its one fallback wakeup (about twenty minutes after an iteration that
   neither reschedules nor stops) are not a plan.
4. **A direct request from the user outranks the normal pick** — the Request
   line above, or a message in the conversation ("do the three leads", an
   answer to a question the notes asked). A ruling in it is recorded first
   (`okf.py ruling`), in the user's words. Do that, in the commits it needs,
   then end the iteration as usual. Nobody is watching the terminal: a
   question asked only in the report is lost, so it goes in `LOOP_NOTES`.

The Stop hook refuses to end a turn whose gates ran after `LOOP_NOTES` was
last written, or while `okf.py check` finds a broken concept: a net, not the
plan.

## What an iteration is

Outside a campaign, an iteration takes **as many leads as it can finish and
verify, one commit each**. One logical change per commit; never a commit that
bundles two unrelated fixes because they were found together. Stop when the
next lead would not fit, not after the first commit.

Inside a campaign (see "Campaigns") the rule inverts: the campaign is a batch
that `BRANCH` receives as one commit when all of it is done, and every iteration
pushes that batch as far as it can.

## Start of every iteration

1. **Run `state.sh` and read it once.** `LOOP_NOTES` MISSING means a fresh
   chain: say so, take the gates on a clean tree as the baseline, and write
   the file from scratch at the end. Notes seeded from another installation
   (they say so, or `state.sh` reports their baseline commit is not in this
   repository) carry that checkout's numbers and leads: re-baseline the same
   way and rewrite them as your own.

2. **A dirty tree** is someone's work in progress: leave it alone, never
   stage it, and measure in an export instead (`gates.sh --export`, which
   unpacks `git archive HEAD` under `SCRATCH`), because numbers taken over
   someone else's uncommitted work are not yours to report.

3. **Account for the commits that are not yours.** `state.sh` lists what
   landed since the commit `LOOP_NOTES` measured at; the user commits by hand
   while iterations run. When a gate number disagrees, rule this out first:
   a foreign commit that adds tests raises the count without anything being
   wrong. A wrong change is fixed forward in a new commit, never by
   rewriting one (see "Commits" for a wrong message).

4. **Verify the last iteration.** Run `gates.sh pytest` (cheap; catches
   flakes); the full `gates.sh` only if steps 2–3 found something or you are
   about to touch what could move flake8 or mypy. Then **re-run the one
   command `What the last iteration changed` recorded** — the probe, the
   benchmark, the `ast` comparison behind its central claim — and compare
   what it prints now with what the notes say it printed: the iteration that
   made the claim believed it, and a wrong claim compounds. Only a claim with
   no runnable command ("the menu is unchanged") goes to a general-purpose
   subagent in the foreground, given the hash, the claim and the relevant
   technique and nothing else, so it re-derives the check in a clean context.

5. **Re-check a lead's evidence before working it.** First `grep -n` its
   file and function in `REJECTED`: a place already examined and left alone
   is not reopened without evidence the entry did not have. Leads go stale
   (coverage that already existed, comments already written): a stale one
   goes to `REJECTED` with what you found, not into a commit.

6. **Pick**, preferring: a broken gate, a bug that affects users, a measured
   slowdown, an incomplete feature, a refactor. An open campaign outranks all
   of these except a broken gate. The task list is in the Reference section.

**Keeping the context small.** A search that would read more than a few
files ("which modules import X", "where is option Y read") goes to an
`Explore` subagent, which returns the answer without the search. Gate and
probe output goes to files under `SCRATCH` and is grepped, never read whole.
Append each finding to `SCRATCH/iteration.txt` as it arrives, one append per
finding: after a compaction it is the only complete record of this
iteration's uncommitted findings. Commands run in `REPO`; never `cd` away
from it (a `cd` outside the project directory is reset anyway), and name
anything under `STATE` by its absolute path.

## Guardrails

The guard (`scripts/guard.sh`, a PreToolUse hook for this session) refuses
what has gone wrong before - stash, push, amending anything but its own
message, staging what you did not name, discarding or checking out what is
the user's, rewriting history or the bundle, the user's real data, a gate
without `timeout`, background commands - and names the rule when it does.
A refusal is not a puzzle to route around: do what the rule says.
Everything below is judgment the guard cannot make.

**Other sessions share this repository.** The user commits by hand while
iterations run. Worktrees you did not create, and branches they have checked
out, are not yours: in the worktree list from `state.sh` everything outside
`.claude/worktrees/` is someone else's (`FOREIGN` in `STATE/config.sh` lists
the ones the guard refuses outright; another one is a question for the
user).

**Nothing may touch the user's real data.** `mcomix/constants.py` resolves
`CONFIG_DIR`, `DATA_DIR` and the paths derived from them at import time, so
setting `HOME` and `XDG_*` is not enough — the constants have to be
reassigned. `test/__init__.py:MComixTest` does it correctly; base every probe
on it. It redirects `DATA_DIR` without creating it. Preference defaults that
name the home directory — the file choosers' last browsed and last saved
folders — are read at import time too, and `MComixTest` points them at its
temporary home. `Gtk.RecentManager.get_default()` writes to
`~/.local/share/recently-used.xbel`: patch it to return a
`Gtk.RecentManager(filename=<temp>)`. Getting this wrong has destroyed a
preferences file, leaked files into the recent list, and left bookmarks in the
user's real bookmark store. The guard only sees paths named in a command; a
probe that opens the real paths from Python is invisible to it.

**Clean up what a test or probe starts.** A window left on screen is
answered by the next test that looks for one. `MComixTest` fails the test that
leaves one ("left on screen: <class>"), so a probe not built on it has to
check for itself. Destroying a file chooser before the main loop has turned
makes GTK put up an error dialog of its own that outlives the chooser. A
widget that starts a worker thread — `_BookArea` once it has items — must be
closed, or the thread parks on a condition and the xdist worker never exits;
the symptom is a suite that never prints its summary while each file passes
on its own.

**Leaving the GTK main loop does not end the process.** MComix' worker threads
are not daemons; only `terminate_program()` stops them. A probe flushes stdout
and calls `os._exit(0)` when it is done.

**A benchmark does not outlast what it measures.** One `xvfb-run`, one
process, the whole matrix inside it; poll for a condition, never sleep. **No
going back to GTK3**: no GTK3 idiom, no shim for both, no fallback.

## Handoff: `LOOP_NOTES`

Rewrite it before you finish, under about 80 lines. It is a working note, not
a changelog — `git log` is the changelog. Sections, in this order:

```markdown
## Gate numbers as of <commit>      (the commit you measured, re-read from
                                     git log just before writing; ends with
                                     "Quiet iterations: N")
## Campaign                         (the open one, its worktree, branch and
                                     progress; or "None open")
## Questions for the user           (what blocks work first, then open
                                     proposals, each dated by the commit it
                                     was raised at; information for the
                                     user goes in the report, not here)
## What the last iteration changed  (the commit range, the user-visible
                                     ones named, and the one claim the next
                                     iteration re-checks: its command and
                                     what it printed)
## Leads worth picking up           (ranked; each with evidence the next
                                     iteration can check: file:line, a
                                     command and what it printed)
## Prompt corrections               (statements in this file the tree
                                     contradicts)
```

The file keeps its frontmatter (`type: Iteration Notes`). A ruling goes to
`DECISIONS` and a dead end to `REJECTED` as they happen,
not here. When a section would push the note past its cap, its durable half
belongs in one of those or `LOOP_TECHNIQUES`, and its settled half in `git
log`. Never drop a question the user has not answered.

## Handoff: `LOOP_TECHNIQUES`

Add to it whenever a probe, harness, command or trap proves itself — anything
that will still be true in twenty iterations — in the concept whose topic it
is, or in a new concept named for what one would search for (the object and
the trap: "xdist: a hang is a worker thread that never stopped"), since
`state.sh` lists exactly those names every iteration. A new concept is a new
file whose frontmatter has `type: Technique`, `title`, `tags` (one of
testing, gtk, code, windows, text), `sources` (`- { resource:
"repo:<path>" }` for each file whose change would make it wrong, not every
file it mentions) and `generated: { by: mcomix-loop/<your model id>, at:
<now, UTC, ISO 8601> }`; a meaningful change moves `generated.at`. Correct
a wrong statement in place, "(corrected at <commit>)"; never delete or
overwrite a concept (the guard refuses). After re-checking one flagged
`[sources changed]`, `okf.py verified <file>` records it. Link another as
`[title](<name>.md)`. Read the relevant concept before writing a probe or a
benchmark. It holds how to measure and test, not what was decided
(`DECISIONS`), what was examined and left alone (`REJECTED`), or facts about
the installation (`STATE/project.md`). Do not prune it to save space: the cap
on `LOOP_NOTES` is exactly why it exists.

## Verification gates

All three, before every commit, by one command:
`${CLAUDE_SKILL_DIR}/scripts/gates.sh [pytest|static|deprecations]
[--tree <dir>] [--export[=<rev>]]`. It prints one line per gate and leaves
the full logs in `SCRATCH/pytest.txt`, `flake8.txt` and `mypy.txt`;
`deprecations` lists the `DeprecationWarning` names the last suite run
reached. What it runs, for probes that need a variant:

```sh
env -u WAYLAND_DISPLAY GDK_BACKEND=x11 timeout -k 5 60 \
    xvfb-run -a python3 -m pytest test/ -q -n 8
timeout -k 5 60  python3 -m flake8 --select=F mcomix/ test/   # must be silent
timeout -k 5 120 python3 -m mypy mcomix                        # must report no issues
```

Run outside `xvfb-run`, the suite hangs rather than failing. `-n 8` is
`WORKERS` from `STATE/config.sh`, measured for the machine; `-n auto` is
slower because worker start-up dominates a suite this short.

**A failure seen only under `-n WORKERS` is a bug until shown otherwise, not
a sharding artefact.** Eight workers change timing and neighbours, which is
exactly what exposes a race or a test that leaves state behind. Run the
failing test under `-n WORKERS` several times on a clean export of the commit,
and read what it waits for. This loop once dismissed a test it had just
written because it passed on its own; under eight workers it failed five runs
in six: it pumped the main loop, which delivered the finish of a scan over an
empty directory, before reading what the scan's start had set. `--dist
loadfile` helps diagnose that kind of failure but does not fix it.

pytest must not lose passes, flake8 must stay silent, and mypy must stay at
zero. The configuration is `--strict` plus `disallow_any_explicit`, so new
code is fully annotated with real types, and an explicit `Any` needs an
`ignore[explicit-any]` whose comment says why.

**Timeouts:** `T_PYTEST` (60 s) for the suite and any probe, `T_MYPY` (120
s) for mypy, from `STATE/config.sh`, as `timeout -k 5 <seconds>` inside the
command — the Bash tool's own timeout backgrounds an overrun instead of
killing it, which hides a hang. A hang (124) is itself a finding. Foreground
only, never `run_in_background`.

## Commits

A `type:` prefix (`fix`, `feat`, `perf`, `refactor`, `test`, `docs`, `i18n`,
`build`, `chore`), a one-line subject naming what was wrong, then prose giving
the cause and the evidence, passed with `-m` or `-F` (a commit without a
message opens an editor, which hangs the loop). Name the files you stage;
never `git add -A`. No trailer of any kind — no `Co-Authored-By`, no
"Generated with", no session link: `attribution` in settings is empty and
the curated history carries none. Write the message after the gates, from
their output: a count typed from memory has been wrong before.

**A message the loop got wrong is corrected, the commit never.** The guard
notes each commit the loop is about to make, its parent and subject, in
`STATE/commits.log`. Its own newest commit (parent and subject noted there),
while nothing is on top of it and no remote branch contains it:
`git commit --amend --only -F <file>` — message only, the tree stays as it
is; the guard allows nothing else under `--amend`. Any other commit:
`git notes append -F <file> <commit>`, which leaves the commit alone;
`git log` shows the note under the message, and the user folds it in when he
next rewrites history by hand. GitHub shows no notes, so a correction that
matters to readers there is also a question for the user.

## Evidence standards

**Measure, don't guess.** Benchmark before calling something slow and after
changing it; both numbers go in the commit message. If the measurement says
the change does not help, drop it and record that.

**Distrust your own probe before the code.** Findings here have been the probe
being wrong: `get_action_area()` read on a dialog that keeps its buttons
elsewhere; `AccelLabel.get_accel()`, which reports only manually set
accelerators and so said "none" for a menu with 72. When a probe says
something surprising, prove the probe first.

**A bug fix has a regression test you watched fail.** Write the test, copy
the fixed file aside, `git checkout HEAD -- <file>`, confirm the test fails,
copy it back, confirm it passes. **A test that fixes nothing is shown to
bite**: break the code it covers, see it fail, restore the code.

**A test of something asynchronous reads the synchronous effect first.** A
signal handler runs inside the emission, but a worker thread's answer comes
back through the idle queue, and the next pump of the main loop delivers it.
Assert what the call set before pumping, then pump and assert what the answer
should have changed.

**A refactor that claims to change nothing proves it.** The pass count is the
same before and after. A move is compared mechanically: parse the old and new
bodies with `ast` and confirm they are identical once the rename is undone.
Before splitting anything, size it by coupling — how many attributes of the
class each group reads, how many sibling methods it calls — and put that table
in the commit message; a group that reaches back for most of the class is not
a separable one, however many lines it has.

**SQL is proven by its plan.** `EXPLAIN QUERY PLAN` on a table that grows with
the library must not say `SCAN`; assert the plan in the test rather than a
duration, and measure at tens of thousands of books.

**A change carries its documentation, reviewed.** A commit that changes
behaviour, an option, a key, a dependency or a release step reads the pages
under `docs/` it touches - the page, not only the sentence, for what is now
wrong or verbose - and fixes them in the same commit; `test/test_wiki.py`,
`test_keybindings.py` and `test_openwith_command.py` fail on a page that
drifted. A `ChangeLog.md` line goes in only where `STATE/project.md` says a
section for the unreleased version is open.

**A new translatable string carries its translations.** Regenerate
`mcomix/messages/mcomix.pot`, merge it into every catalogue under
`mcomix/messages/`, translate the new entries, and compile every `.mo`, all
in the same commit; `test/test_messages.py` fails otherwise
(`docs/development.md`; the commands are in the translation techniques).

## Campaigns

A campaign is work too large for one commit that is still one change — a
toolkit migration, a typing pass over the whole tree. It lands on the branch
the checkout is on (`state.sh` names it; `BRANCH` below) as a single squashed
commit when all of it is done.

**Opening one is the user's decision**: propose it under `Questions for the
user` with a size estimate. **It is carried in a worktree of its own**,
because loose files in `REPO` have been swallowed by the user's amends; it
lives under `.claude/worktrees/`, which `.git/info/exclude` hides:

```sh
git worktree add -b loop/<campaign> .claude/worktrees/campaign BRANCH
```

Record the branch under `## Campaign` in `LOOP_NOTES`. Commit every
verifiable step to the branch — those commits are scratch, for the next
iteration to read with `git log loop/<campaign>` — and run every gate inside
the worktree (`gates.sh --tree .claude/worktrees/campaign`). Never
`EnterWorktree` and never `cd` into it: the guard and `state.sh` assume the
working directory is `REPO`; address it with `git -C`. To land it:

```sh
git -C .claude/worktrees/campaign rebase BRANCH   # then the gates again, there
git merge --squash loop/<campaign>
git commit -F <message file>                      # one message for the whole
git worktree remove .claude/worktrees/campaign && git branch -D loop/<campaign>
```

If the merge meets the user's changes to the same lines, resolve in their
favour and run the gates again. Never rebase or amend anything of theirs.

Work one campaign at a time and pick nothing else while it is open. Fan work
out to subagents only where the units are independent — modules that do not
import one another — and merge the branches back into `loop/<campaign>` one
at a time with the gates run over the union. Pieces that share scaffolding,
such as several views over one model, stay in one thread. A subagent with
`isolation: "worktree"` branches from `BRANCH` (only because
`worktree.baseRef` is `head` in settings), not from the campaign branch; to
start a unit from the campaign branch, make its worktree yourself —
`git worktree add -b loop/<campaign>-<unit> .claude/worktrees/campaign-<unit>
loop/<campaign>` — and name the path in its task.

## Reporting

The report is terse: what was committed, measured, checked and rejected, and
whether the loop continues. Numbers and hashes exact; no tool-call narration;
never a dropped `not`, `only` or `except`; plain prose where compression would
make a warning or an ordered sequence ambiguous. A caveman style injected by
its plugin applies on top (do not restate or announce it). Everything written
down - commits, code, comments, the bundle, docs, catalogues - is ordinary
English prose, for readers who never saw the terminal.

## Reference

The task list and the facts of the code base, from `reference.md` beside
this file; the facts of this installation from `state/project.md`, which
the user maintains; the user's rulings from `state/decisions/`, one line
each. This tail
is what a compaction drops: Read them again (`okf.py rulings` for the
rulings) when you need them afterwards.

!`cat "${CLAUDE_SKILL_DIR}/reference.md"`

### This installation

!`cat "${CLAUDE_SKILL_DIR}/state/project.md" 2>/dev/null || echo "(no state/project.md yet: no installation facts, no finished campaigns)"`

### The user's rulings

!`python3 "${CLAUDE_SKILL_DIR}/scripts/okf.py" rulings 2>/dev/null || echo "(no rulings recorded)"`
