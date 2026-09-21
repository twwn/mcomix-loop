#!/usr/bin/env bash
# Verification gates for the MComix loop.
#
#   gates.sh [pytest|static|all|deprecations] [--tree <dir>] [--export[=<rev>]]
#
#   all (default)   pytest under xvfb-run -n 8, flake8 --select=F, mypy
#   pytest          the suite only
#   static          flake8 and mypy only
#   deprecations    DeprecationWarning names the last pytest log reached (no run)
#   --tree <dir>    run in <dir> instead of the checkout (a campaign worktree)
#   --export[=rev]  run on a clean `git archive` of <rev> (default HEAD) of the
#                   main repository, unpacked under the scratch directory
#
# Exit 0 when every gate that ran passed, 1 otherwise, 2 on a usage error.
# Full logs: <skill>/state/scratch/{pytest,flake8,mypy}.txt
#
# The timeouts are `timeout -k 5` inside the command on purpose: the Bash
# tool's own timeout moves an overrunning command to the background instead
# of killing it, so only this surfaces a hang (exit 124).

set -u

. "$(dirname "$0")/paths.sh"
REPO=$(resolve_repo) || { echo "gates: $PWD is not an MComix checkout (mcomix/, test/, mcomix/constants.py); start claude in one" >&2; exit 2; }

mode=all
tree=$REPO
export_rev=""

while [ $# -gt 0 ]; do
    case "$1" in
        pytest|static|all|deprecations) mode=$1 ;;
        --tree) shift; tree=${1:?--tree needs a directory} ;;
        --tree=*) tree=${1#--tree=} ;;
        --export) export_rev=HEAD ;;
        --export=*) export_rev=${1#--export=} ;;
        -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
        *) echo "gates: unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

mkdir -p "$SCRATCH"

if [ "$mode" = deprecations ]; then
    if [ ! -s "$SCRATCH/pytest.txt" ]; then
        echo "gates: no pytest log in $SCRATCH; run the suite first" >&2
        exit 2
    fi
    echo "deprecations reached by the last suite run ($(stat -c %y "$SCRATCH/pytest.txt" | cut -d. -f1)):"
    grep -oP 'DeprecationWarning: \S+' "$SCRATCH/pytest.txt" | sort -u
    exit 0
fi

if [ -n "$export_rev" ]; then
    sha=$(git -C "$REPO" rev-parse --short "$export_rev") || exit 2
    tree=$EXPORT_DIR/export-$sha
    rm -rf "$EXPORT_DIR"/export-*                    # one export at a time
    mkdir -p "$tree"
    git -C "$REPO" archive "$export_rev" | tar -x -C "$tree" || exit 2
    echo "export: $export_rev ($sha) unpacked at $tree"
fi

case "$tree" in /*) ;; *) tree=$REPO/$tree ;; esac         # --tree may be relative to the checkout
cd "$tree" || { echo "gates: cannot cd to $tree" >&2; exit 2; }

# Stamp for the Stop hook: the gates ran now; LOOP_NOTES must be newer by the
# end of the iteration. Reset the hook's block counter for this run.
: > "$SCRATCH/gates.stamp"
rm -f "$SCRATCH/stop-blocks"

status=0

if [ "$mode" = all ] || [ "$mode" = pytest ]; then
    env -u WAYLAND_DISPLAY GDK_BACKEND=x11 timeout -k 5 "$T_PYTEST" \
        xvfb-run -a python3 -m pytest test/ -q -n "$WORKERS" \
        > "$SCRATCH/pytest.txt" 2>&1
    rc=$?
    # Grep, never tail: the summary line is interleaved with warning output.
    summary=$(grep -E '[0-9]+ (passed|failed|error)' "$SCRATCH/pytest.txt" | tail -1)
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
        echo "pytest: HUNG, killed after ${T_PYTEST}s (a hang is a finding); last line: $(tail -1 "$SCRATCH/pytest.txt")"
        status=1
    elif [ "$rc" -ne 0 ] || [ -z "$summary" ]; then
        echo "pytest: FAILED (exit $rc): ${summary:-no summary line; see $SCRATCH/pytest.txt}"
        status=1
    else
        echo "pytest: $summary"
    fi
fi

if [ "$mode" = all ] || [ "$mode" = static ]; then
    timeout -k 5 "$T_FLAKE8" python3 -m flake8 --select=F mcomix/ test/ \
        > "$SCRATCH/flake8.txt" 2>&1
    rc=$?
    if [ "$rc" -eq 124 ]; then
        echo "flake8: HUNG, killed after ${T_FLAKE8}s"; status=1
    elif [ "$rc" -ne 0 ] || [ -s "$SCRATCH/flake8.txt" ]; then
        echo "flake8: $(wc -l < "$SCRATCH/flake8.txt") lines (exit $rc); first: $(head -1 "$SCRATCH/flake8.txt")"
        status=1
    else
        echo "flake8: silent"
    fi

    timeout -k 5 "$T_MYPY" python3 -m mypy mcomix > "$SCRATCH/mypy.txt" 2>&1
    rc=$?
    if [ "$rc" -eq 124 ]; then
        echo "mypy: HUNG, killed after ${T_MYPY}s"; status=1
    elif [ "$rc" -ne 0 ]; then
        echo "mypy: FAILED (exit $rc): $(tail -1 "$SCRATCH/mypy.txt")"
        status=1
    else
        echo "mypy: $(tail -1 "$SCRATCH/mypy.txt")"
    fi
fi

echo "tree: $tree at $(git -C "$tree" rev-parse --short HEAD 2>/dev/null || echo 'no git'); logs: $SCRATCH"
exit $status
