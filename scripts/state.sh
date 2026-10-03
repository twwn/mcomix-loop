#!/usr/bin/env bash
# First command of every loop iteration: prints the state the skill body used
# to inject. Kept out of SKILL.md on purpose — the harness re-appends a skill's
# whole body whenever its rendered text changes, so a state block inside the
# skill re-bought the entire prompt every iteration. Read-only; output is meant
# to be read once, not grepped.

set -u
case "$0" in */*) . "${0%/*}/paths.sh" ;; *) . ./paths.sh ;; esac
REPO=$(resolve_repo) || { echo "state: $PWD is not an MComix checkout (mcomix/, test/, mcomix/constants.py). Start claude in one; the loop does nothing elsewhere." >&2; exit 2; }
is_gtk4 "$REPO" || { echo "state: $REPO does not require Gtk 4.0 anywhere under mcomix/; this loop targets the GTK4 port and its rules are wrong for a GTK3 tree." >&2; exit 2; }
CAMPAIGN=$REPO/.claude/worktrees/campaign
mkdir -p "$SCRATCH"

g() { git -C "$REPO" "$@" 2>/dev/null; }

echo "== repo: $REPO on branch $(g symbolic-ref --short -q HEAD || echo "(detached at $(g rev-parse --short HEAD))") =="
echo "== state: $STATE (workers $WORKERS; timeouts $T_PYTEST/$T_FLAKE8/$T_MYPY s) =="
echo "== tree =="
st=$(g status --short)
[ -n "$st" ] && printf '%s\n' "$st" || echo "clean"

echo "== commits =="
base=$(sed -nE 's/^## Gate numbers as of ([0-9a-f]{7,40}).*/\1/p' "$NOTES" 2>/dev/null | head -1)
if [ -n "$base" ] && g cat-file -e "$base^{commit}"; then
    since=$(g log --oneline "$base..HEAD")
    if [ -n "$since" ]; then
        echo "since the notes' baseline $base (not yours unless the notes say so):"
        printf '%s\n' "$since"
    else
        echo "none since the notes' baseline $base"
    fi
    echo "HEAD: $(g log --oneline -1)"
else
    [ -n "$base" ] && echo "baseline $base from the notes is not in this repository; last 20:"
    g log --oneline -20
fi

echo "== worktrees =="
g worktree list
echo "== loop/* branches =="
b=$(g branch --list 'loop/*'); [ -n "$b" ] && printf '%s\n' "$b" || echo "none"
[ -e "$CAMPAIGN" ] && echo "campaign worktree present: $CAMPAIGN"

echo "== LOOP_NOTES =="
if [ -e "$NOTES" ]; then awk 'NR == 1 && /^---$/ { fm = 1; next } fm && /^---$/ { fm = 0; next } !fm' "$NOTES"
else echo "MISSING (fresh chain: baseline the gates on a clean tree, write the file from scratch at the end)"; fi

echo "== LOOP_TECHNIQUES: $TECHNIQUES/<name>.md =="
$OKF state || echo "(okf.py state failed; the bundle may be unreadable)"

echo "== protocol =="
echo "Before a lead: grep -rn its file and function in $REJECTED. A ruling from the user: record it with okf.py ruling, in their words, then act."
echo "End: rewrite LOOP_NOTES, add to LOOP_TECHNIQUES/REJECTED, delete iteration.txt, report, ScheduleWakeup last (60 s; up to 900 while only a CI run is awaited; stop only for 3 quiet / unfixable gate / user's decision, with PushNotification)."
echo "Never: stash, push, add -A, background commands, suite/probe/mypy without timeout; amend only your own unpushed tip, message only. Findings as they arrive -> $SCRATCH/iteration.txt."
