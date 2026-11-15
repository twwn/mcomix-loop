# Sourced by every script in this directory. Nothing here is fixed to /tmp:
#
#   REPO      the MComix checkout = the directory `claude` was started in
#             (hooks get it as $CLAUDE_PROJECT_DIR or the hook input's cwd;
#             tool commands get it as $PWD). Verified by fingerprint.
#   STATE     $SKILL_DIR/state — the loop's memory, an Open Knowledge Format
#             (OKF 0.2) bundle kept beside the skill (scripts/okf.py reads and
#             checks it). Gitignored, so a reinstall does not touch it.
#   NOTES      $STATE/notes.md         LOOP_NOTES, rewritten every iteration
#   TECHNIQUES $STATE/techniques/      LOOP_TECHNIQUES, one concept per file
#   DECISIONS  $STATE/decisions/       the user's rulings, one file each; never edited by the loop
#   REJECTED   $STATE/rejected.md      what was examined and left alone
#   COMMITS    $STATE/commits.log      parent and subject of each commit the loop made (guard.sh)
#   SCRATCH    $STATE/scratch          gate logs, exports, iteration.txt; not part of the bundle
#   SESSIONS   $SCRATCH/sessions       one empty file per session the guard has run in (subagent-guard.sh)
#   SWEEP      $SCRATCH/sweep          the open sweep's briefs, probes and reports (sweep.sh)
#   SWEEPS     $STATE/sweeps.log       what each lens of each sweep returned, what survived, at what model and effort, and what it took of the 5-hour window (sweep.sh)
#   USAGE      $SCRATCH/usage          the plan's usage windows as the status line last read them (statusline.sh)
#   CAMPAIGN  $REPO/.claude/worktrees/campaign — inside the project directory,
#             next to where the harness puts subagent worktrees, so no extra
#             permission scope is needed; .claude/ must be in .git/info/exclude.
#
# is_gtk4 <dir>: the loop targets the GTK4 port; upstream 3.x is GTK3 and
# every rule about widgets, deprecations and dependencies would be wrong there.

# Every hook and tool command calls the scripts by absolute path; only a
# relative call (a script run by hand) pays for the subshell.
SKILL_DIR=${BASH_SOURCE[0]%/*}
case "$SKILL_DIR" in
    /*/scripts) SKILL_DIR=${SKILL_DIR%/scripts} ;;
    *) SKILL_DIR=$(cd "$SKILL_DIR/.." && pwd) ;;
esac
STATE=$SKILL_DIR/state
NOTES=$STATE/notes.md
TECHNIQUES=$STATE/techniques
DECISIONS=$STATE/decisions
REJECTED=$STATE/rejected.md
COMMITS=$STATE/commits.log
SCRATCH=$STATE/scratch
SESSIONS=$SCRATCH/sessions
SWEEP=$SCRATCH/sweep
SWEEPS=$STATE/sweeps.log
USAGE=$SCRATCH/usage
OKF="python3 -S $SKILL_DIR/scripts/okf.py"   # -S: stdlib only, and site's start-up is two thirds of its run

# Per-installation settings, overridable in $STATE/config.sh (seeded from
# base/config.sh; the guard treats that file as the user's, not the loop's).
WORKERS=8          # pytest-xdist workers; measure it, -n auto is slower on a short suite
T_PYTEST=60        # seconds; the suite and any probe
T_FLAKE8=60
T_MYPY=120
FOREIGN=()         # checkouts other sessions own (absolute paths); refused by the guard
EXPORT_DIR=$SCRATCH   # where `gates.sh --export` unpacks a tree; a short path on Python 3.12, or 3.13 before 3.13.6
ISSUES_REPO=""     # owner/name whose issues the loop may write with gh; empty: none
ISSUES_PROJECT=""  # owner/number of the GitHub project whose items it may write; empty: none
SWEEP_EVERY=25     # commits under mcomix/ or docs/ before a lens that found nothing runs again; 0: no sweeps
SWEEP_RETIRE=3     # empty runs in a row that retire a lens: it then rests SWEEP_EVERY commits per empty run; 0: never
SWEEP_WIDTH=5      # auditors at once
SWEEP_MODEL=sonnet # the model and effort of an auditor, unless the sweep names another for its lens
SWEEP_EFFORT=high
SWEEP_FEATURES=0   # 1: a sweep may also look for what MComix lacks (the feature lenses in sweep.md)
SWEEP_CALLS=40     # tool calls an auditor stops at; each reads again all the calls before it
SWEEP_LENS_COST=7  # percent of the 5-hour window one lens takes, until sweeps.log has measured it
WINDOW_RESERVE=10  # percent of the 5-hour window kept for finishing an iteration; past 100 minus this, nothing new starts
WEEK_RESERVE=15    # percent of the 7-day window left to the user's own sessions; past 100 minus this, nothing new starts
# shellcheck disable=SC1091
[ -r "$STATE/config.sh" ] && . "$STATE/config.sh"

# window: the plan's 5-hour and 7-day windows, from the status line's last
# reading. Sets W_PCT (percent used) and W_RESET (Unix seconds), W7_PCT and
# W7_RESET, and W_AGE (seconds since the reading); each is - when unknown. A
# window that has reset since the reading counts as 0 used, its reset unknown.
window() {
    local at="" p="" r="" p7="" r7="" rest now
    printf -v now '%(%s)T' -1
    [ -r "$USAGE" ] && IFS=$'\t' read -r at p r p7 r7 rest < "$USAGE"
    W_PCT=- W_RESET=- W7_PCT=- W7_RESET=- W_AGE=-
    [[ "$at" =~ ^[0-9]+$ ]] || return 0
    W_AGE=$((now - at))
    if [[ "$p" =~ ^[0-9]+$ && "$r" =~ ^[0-9]+$ ]]; then
        if [ "$r" -gt "$now" ]; then W_PCT=$p W_RESET=$r; else W_PCT=0; fi
    fi
    if [[ "$p7" =~ ^[0-9]+$ && "$r7" =~ ^[0-9]+$ ]]; then
        if [ "$r7" -gt "$now" ]; then W7_PCT=$p7 W7_RESET=$r7; else W7_PCT=0; fi
    fi
    return 0
}

# window_wake [reset]: the delaySeconds that wakes the loop a minute after a
# window resets (the 5-hour one unless another reset is given), within
# ScheduleWakeup's 60 to 3600; 3600 when the reset is unknown.
window_wake() {
    local now s=3600 r=${1:-$W_RESET}
    printf -v now '%(%s)T' -1
    [[ "$r" =~ ^[0-9]+$ ]] && s=$((r - now + 60))
    [ "$s" -ge 60 ] || s=60
    [ "$s" -le 3600 ] || s=3600
    echo "$s"
}

# statusline_set: the settings run statusline.sh, which keeps the reading.
statusline_set() {
    grep -qsF statusline.sh "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" "$1/.claude/settings.json" "$1/.claude/settings.local.json"
}

# subagents_guarded <checkout>: the settings name the hook that guards subagents.
# It reads only the text: a session started before the merge may not have the hook yet.
subagents_guarded() {
    grep -qsF subagent-guard.sh "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" "$1/.claude/settings.json" "$1/.claude/settings.local.json"
}

# is_mcomix <dir>: the fingerprint of a checkout this loop may work on.
is_mcomix() {
    [ -d "$1/.git" ] || [ -f "$1/.git" ] || return 1     # a worktree has a .git file
    [ -d "$1/mcomix" ] && [ -d "$1/test" ] && [ -f "$1/mcomix/constants.py" ]
}

is_gtk4() {
    grep -rqsE "require_version\(['\"]Gtk['\"], *['\"]4\.0['\"]\)" "$1/mcomix"
}

# resolve_repo [dir]: the checkout's top level, from the first of: the
# argument, $CLAUDE_PROJECT_DIR (set for hooks), $PWD. Prints it, or fails.
# The top level is the nearest directory upwards with a .git, found without
# starting git: the guard runs this on every tool call.
resolve_repo() {
    local d top
    for d in "${1:-}" "${CLAUDE_PROJECT_DIR:-}" "$PWD"; do
        [ -n "$d" ] || continue
        case "$d" in /*) ;; *) d=$PWD/$d ;; esac
        top=${d%/}
        until [ -e "$top/.git" ] || [ -z "$top" ]; do top=${top%/*}; done
        [ -n "$top" ] || continue
        # A campaign worktree resolves to itself; walk up to the main checkout.
        case "$top" in */.claude/worktrees/*) top=${top%%/.claude/worktrees/*} ;; esac
        if is_mcomix "$top"; then printf '%s\n' "$top"; return 0; fi
    done
    return 1
}
