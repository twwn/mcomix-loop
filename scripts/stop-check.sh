#!/usr/bin/env bash
# Stop hook for the MComix loop (registered by SKILL.md).
#
# An iteration that ran the gates must rewrite LOOP_NOTES afterwards. gates.sh
# writes a stamp on every run, naming the session and the checkout it ran
# for; if LOOP_NOTES is older than this session's stamp when Claude tries to
# end the turn, exit 2 keeps the turn going with the reason on stderr. At
# most two blocks per gate run (counter reset by gates.sh), and none when the
# harness says a Stop hook already continued this turn.
#
# A session whose working directory is not an MComix checkout is never held
# back: it invoked the skill without running the loop (to read it, say), and
# the gate runs it would see are another session's.

set -u
case "$0" in */*) . "${0%/*}/paths.sh" ;; *) . ./paths.sh ;; esac
STAMP=$SCRATCH/gates.stamp
COUNTER=$SCRATCH/stop-blocks
CHECKED=$SCRATCH/okf-checked

if command -v jq >/dev/null 2>&1; then
    fields() { jq -j '[.stop_hook_active, .session_id, .cwd] | map((. // "" | tostring) + "\u0000") | add' 2>/dev/null; }
else
    fields() { python3 -S -c 'import json, sys
d = json.load(sys.stdin)
v = [d.get("stop_hook_active"), d.get("session_id"), d.get("cwd")]
sys.stdout.write("".join(("true" if x is True else "" if x in (None, False) else str(x)) + "\0" for x in v))' 2>/dev/null; }
fi
{ IFS= read -r -d '' active; IFS= read -r -d '' session; IFS= read -r -d '' cwd; } < <(fields)
[ "$active" = true ] && exit 0
REPO=$(resolve_repo "${cwd:-}") || exit 0

# The bundle must stay readable: a concept with broken frontmatter drops out
# of every listing, and a ruling without one is not injected at all. Checked
# again only when a concept or a directory of the bundle changed after the
# last clean check; the stamp is taken before the check, so a write during it
# counts as a change.
changed=yes
if [ -e "$CHECKED" ]; then
    changed=$(find "$STATE" \( -path "$SCRATCH" -o -path "$STATE/probes" \) -prune \
        -o -newer "$CHECKED" \( -name '*.md' -o -type d \) -print -quit 2>/dev/null)
fi
if [ -n "$changed" ]; then
    mkdir -p "$SCRATCH"; : > "$CHECKED.new"
    problems=$($OKF check 2>/dev/null)
    if [ -n "$problems" ]; then
        rm -f "$CHECKED.new"
        n=$(cat "$SCRATCH/okf-blocks" 2>/dev/null || echo 0)
        if [ "$n" -lt 2 ]; then
            echo $((n + 1)) > "$SCRATCH/okf-blocks"
            printf 'mcomix-loop: the knowledge bundle has problems; fix them before ending the turn:\n%s\n' "$problems" >&2
            exit 2
        fi
    else
        mv "$CHECKED.new" "$CHECKED"
        rm -f "$SCRATCH/okf-blocks"
    fi
fi

[ -e "$STAMP" ] || exit 0                       # no gate run this iteration: nothing to check
# Whose gate run: the session gates.sh ran in (the Bash tool passes it
# CLAUDE_CODE_SESSION_ID) and the checkout. A stamp without them (an older
# gates.sh) counts as this session's.
IFS=$'\t' read -r stamp_session stamp_repo < "$STAMP"
[ -n "${stamp_session:-}" ] && [ -n "$session" ] && [ "$stamp_session" != "$session" ] && exit 0
[ -n "${stamp_repo:-}" ] && [ "$stamp_repo" != "$REPO" ] && exit 0

if [ ! -e "$NOTES" ] || [ "$STAMP" -nt "$NOTES" ]; then
    n=$(cat "$COUNTER" 2>/dev/null || echo 0)
    [ "$n" -ge 2 ] && exit 0                    # already blocked twice for this gate run; let it end
    echo $((n + 1)) > "$COUNTER"
    echo "mcomix-loop: the gates ran after LOOP_NOTES was last written. Rewrite $NOTES (all sections, gate numbers as of the commit you measured), add to LOOP_TECHNIQUES or REJECTED what proved itself, then ScheduleWakeup." >&2
    exit 2
fi
rm -f "$COUNTER"
exit 0
