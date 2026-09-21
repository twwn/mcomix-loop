#!/usr/bin/env bash
# First command of every loop iteration: prints the state the skill body used
# to inject. Kept out of SKILL.md on purpose — the harness re-appends a skill's
# whole body whenever its rendered text changes, so a state block inside the
# skill re-bought the entire prompt every iteration. Read-only; output is meant
# to be read once, not grepped.

set -u
. "$(dirname "$0")/paths.sh"
REPO=$(resolve_repo) || { echo "state: $PWD is not an MComix checkout (mcomix/, test/, mcomix/constants.py). Start claude in one; the loop does nothing elsewhere." >&2; exit 2; }
is_gtk4 "$REPO" || { echo "state: $REPO does not require Gtk 4.0 anywhere under mcomix/; this loop targets the GTK4 port and its rules are wrong for a GTK3 tree." >&2; exit 2; }
CAMPAIGN=$REPO/.claude/worktrees/campaign
mkdir -p "$SCRATCH"

g() { git -C "$REPO" "$@" 2>/dev/null; }

echo "== repo: $REPO =="
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
cat "$NOTES" 2>/dev/null || echo "MISSING (fresh chain: baseline the gates on a clean tree, write the file from scratch at the end)"

echo "== LOOP_TECHNIQUES sections =="
grep -nE '^## ' "$TECHNIQUES" 2>/dev/null || echo "MISSING"
missing=$(grep -oE 'STATE/probes/[A-Za-z0-9_./-]+' "$TECHNIQUES" 2>/dev/null | sed 's/[.]*$//' | sort -u | while read -r ref; do
    [ -e "$STATE/${ref#STATE/}" ] || printf '%s ' "$ref"
done)
[ -n "$missing" ] && echo "probes named above but not on disk (rebuild from the description before use): $missing"

echo "== protocol =="
echo "End: rewrite LOOP_NOTES, append LOOP_TECHNIQUES, delete iteration.md, report, ScheduleWakeup last (60 s; stop only for 3 quiet / unfixable gate / user's decision, with PushNotification)."
echo "Never: stash, push, amend, add -A, background commands, suite/probe/mypy without timeout. Findings as they arrive -> $SCRATCH/iteration.md."
