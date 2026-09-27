#!/usr/bin/env bash
# Stop hook for the MComix loop (registered by SKILL.md).
#
# An iteration that ran the gates must rewrite LOOP_NOTES afterwards. gates.sh
# touches a stamp on every run; if LOOP_NOTES is older than that stamp when
# Claude tries to end the turn, exit 2 keeps the turn going with the reason on
# stderr. At most two blocks per gate run (counter reset by gates.sh), and
# none when the harness says a Stop hook already continued this turn.

set -u
. "$(dirname "$0")/paths.sh"
STAMP=$SCRATCH/gates.stamp
COUNTER=$SCRATCH/stop-blocks

input=$(cat)
if command -v jq >/dev/null 2>&1; then
    active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)
else
    active=$(printf '%s' "$input" | python3 -c 'import json,sys; print(str(json.load(sys.stdin).get("stop_hook_active", False)).lower())' 2>/dev/null)
fi
[ "$active" = true ] && exit 0

# The bundle must stay readable: a concept with broken frontmatter drops out
# of every listing, and a ruling without one is not injected at all.
problems=$($OKF check 2>/dev/null)
if [ -n "$problems" ]; then
    n=$(cat "$SCRATCH/okf-blocks" 2>/dev/null || echo 0)
    if [ "$n" -lt 2 ]; then
        mkdir -p "$SCRATCH"; echo $((n + 1)) > "$SCRATCH/okf-blocks"
        printf 'mcomix-loop: the knowledge bundle has problems; fix them before ending the turn:\n%s\n' "$problems" >&2
        exit 2
    fi
else
    rm -f "$SCRATCH/okf-blocks"
fi

[ -e "$STAMP" ] || exit 0                       # no gate run this iteration: nothing to check

if [ ! -e "$NOTES" ] || [ "$STAMP" -nt "$NOTES" ]; then
    n=$(cat "$COUNTER" 2>/dev/null || echo 0)
    [ "$n" -ge 2 ] && exit 0                    # already blocked twice for this gate run; let it end
    echo $((n + 1)) > "$COUNTER"
    echo "mcomix-loop: the gates ran after LOOP_NOTES was last written. Rewrite $NOTES (all sections, gate numbers as of the commit you measured), add to LOOP_TECHNIQUES or REJECTED what proved itself, then ScheduleWakeup." >&2
    exit 2
fi
rm -f "$COUNTER"
exit 0
