# Sourced by every script in this directory. Nothing here is fixed to /tmp:
#
#   REPO      the MComix checkout = the directory `claude` was started in
#             (hooks get it as $CLAUDE_PROJECT_DIR or the hook input's cwd;
#             tool commands get it as $PWD). Verified by fingerprint.
#   STATE     $SKILL_DIR/state — the loop's memory, kept beside the skill so
#             it survives a reboot and moves with the skill. Never shipped
#             with the bundle, so a reinstall does not touch it.
#   NOTES     $STATE/notes.md        (LOOP_NOTES)
#   TECHNIQUES $STATE/techniques.md  (LOOP_TECHNIQUES)
#   SCRATCH   $STATE/scratch         gate logs, exports, iteration.md
#   CAMPAIGN  $REPO/.claude/worktrees/campaign — inside the project directory,
#             next to where the harness puts subagent worktrees, so no extra
#             permission scope is needed; .claude/ must be in .git/info/exclude.
#
# is_gtk4 <dir>: the loop targets the GTK4 port; upstream 3.x is GTK3 and
# every rule about widgets, deprecations and dependencies would be wrong there.

SKILL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
STATE=$SKILL_DIR/state
NOTES=$STATE/notes.md
TECHNIQUES=$STATE/techniques.md
SCRATCH=$STATE/scratch

# Per-installation settings, overridable in $STATE/config.sh (see
# config.example.sh at the top level; the guard treats that file as the
# user's, not the loop's).
WORKERS=8          # pytest-xdist workers; measure it, -n auto is slower on a short suite
T_PYTEST=60        # seconds; the suite and any probe
T_FLAKE8=60
T_MYPY=120
FOREIGN=()         # checkouts other sessions own (absolute paths); refused by the guard
EXPORT_DIR=$SCRATCH   # where `gates.sh --export` unpacks a tree; a short path on Python < 3.14
# shellcheck disable=SC1091
[ -r "$STATE/config.sh" ] && . "$STATE/config.sh"

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
resolve_repo() {
    local d top
    for d in "${1:-}" "${CLAUDE_PROJECT_DIR:-}" "$PWD"; do
        [ -n "$d" ] || continue
        top=$(git -C "$d" rev-parse --show-toplevel 2>/dev/null) || continue
        # A campaign worktree resolves to itself; walk up to the main checkout.
        case "$top" in */.claude/worktrees/*) top=${top%%/.claude/worktrees/*} ;; esac
        if is_mcomix "$top"; then printf '%s\n' "$top"; return 0; fi
    done
    return 1
}
