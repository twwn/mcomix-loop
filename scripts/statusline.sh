#!/usr/bin/env bash
# Status line for Claude Code (statusLine in settings-snippet.json). Claude Code
# passes the session's state as JSON on stdin. This keeps the plan's usage
# windows from it in $SCRATCH/usage, which state.sh and sweep.sh read, and
# prints one line: the 5-hour and 7-day windows and the context.
#
#   statusline.sh           keep the reading, print the line
#   statusline.sh --quiet   keep the reading only, for a status line of your
#                           own that passes its input on to this script
#
# The windows are the account's, not the session's: any session's reading
# serves the loop, and the user's own sessions draw on the same windows.
# Claude Code reports them only on a subscription, after a session's first
# response. The file is one tab-separated line: the time of the reading, the
# 5-hour window's percent used (rounded up) and reset (Unix seconds), the
# 7-day window's; `-` for one not reported. It is written only when a window
# is reported, through a temporary file, so that a reader never sees half a line.

set -u
quiet=""; [ "${1:-}" = --quiet ] && quiet=1
d=${BASH_SOURCE[0]%/*}; [ "$d" = "${BASH_SOURCE[0]}" ] && d=.
# A status line runs in every session: without the skill's scripts it prints nothing.
[ -r "$d/paths.sh" ] || exit 0
# shellcheck source=paths.sh
. "$d/paths.sh"

input=$(cat)
if command -v jq >/dev/null 2>&1; then
    fields=$(jq -r '[.rate_limits.five_hour.used_percentage, .rate_limits.five_hour.resets_at,
        .rate_limits.seven_day.used_percentage, .rate_limits.seven_day.resets_at, .context_window.used_percentage]
        | map(if type == "number" then ceil | tostring else "-" end) | join("\t")' <<< "$input" 2>/dev/null)
else
    fields=$(python3 -S -c 'import json, math, sys
try:
    d = json.loads(sys.stdin.read())
except ValueError:
    sys.exit(1)
def get(*keys):
    v = d
    for k in keys:
        v = v.get(k) if isinstance(v, dict) else None
    return str(math.ceil(v)) if isinstance(v, (int, float)) and not isinstance(v, bool) else "-"
r = ("rate_limits",)
print("\t".join([get(*r, "five_hour", "used_percentage"), get(*r, "five_hour", "resets_at"),
    get(*r, "seven_day", "used_percentage"), get(*r, "seven_day", "resets_at"), get("context_window", "used_percentage")]))' <<< "$input" 2>/dev/null)
fi
IFS=$'\t' read -r p5 r5 p7 r7 ctx <<< "${fields:--	-	-	-	-}"

if [ "$p5$p7" != -- ]; then
    mkdir -p "$SCRATCH" 2>/dev/null
    printf '%(%s)T\t%s\t%s\t%s\t%s\n' -1 "$p5" "$r5" "$p7" "$r7" > "$USAGE.$$" 2>/dev/null \
        && mv -f "$USAGE.$$" "$USAGE" 2>/dev/null
    rm -f "$USAGE.$$" 2>/dev/null
fi

[ -z "$quiet" ] || exit 0
line=""
if [ "$p5" != - ]; then
    line="5h $p5%"
    [ "$r5" != - ] && line+=" to $(printf '%(%H:%M)T' "$r5")"
fi
[ "$p7" != - ] && line+="${line:+ · }7d $p7%"
[ "${ctx:--}" != - ] && line+="${line:+ · }ctx $ctx%"
printf '%s\n' "$line"
