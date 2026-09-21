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
[ -e "$STAMP" ] || exit 0                       # no gate run this iteration: nothing to check

if [ ! -e "$NOTES" ] || [ "$STAMP" -nt "$NOTES" ]; then
    n=$(cat "$COUNTER" 2>/dev/null || echo 0)
    [ "$n" -ge 2 ] && exit 0                    # already blocked twice for this gate run; let it end
    echo $((n + 1)) > "$COUNTER"
    echo "mcomix-loop: the gates ran after LOOP_NOTES was last written. Rewrite $NOTES (all sections, gate numbers as of the commit you measured), append to LOOP_TECHNIQUES if anything proved itself, then ScheduleWakeup." >&2
    exit 2
fi
rm -f "$COUNTER"
exit 0
