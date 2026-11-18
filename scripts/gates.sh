#!/usr/bin/env bash
# Verification gates for the MComix loop.
#
#   gates.sh [pytest|static|all|deprecations] [--tree <dir>] [--export[=<rev>]]
#
#   all (default)   pytest as below, then flake8 --select=F beside mypy
#   pytest          the suite only, then the touched test files twice more:
#                   under the floors venv and on two processors (see below)
#   static          flake8 and mypy only, side by side
#   deprecations    DeprecationWarning names the last pytest log reached (no run)
#   --tree <dir>    run in <dir> instead of the checkout (a campaign worktree)
#   --export[=rev]  run on a clean `git archive` of <rev> (default HEAD) of the
#                   main repository, unpacked under the scratch directory
#
# Exit 0 when every gate that ran passed, 1 otherwise, 2 on a usage error.
# Full logs: <skill>/state/scratch/{pytest,flake8,mypy}.txt; for a --tree other
# than the checkout, <skill>/state/scratch/logs/<tree>/, so that gates running
# at once in two worktrees (subagents of a campaign) keep their logs apart. The
# last line names the directory.
#
# A tree under the scratch or export directory shares one mypy cache,
# <skill>/state/scratch/mypy-cache. An export is new every time, and mypy
# took 24 s on one without a cache, under a second with one. The cache checks
# every module against its source, so trees can share it.
#
# The timeouts are `timeout -k 5` inside the command on purpose: the Bash
# tool's own timeout moves an overrunning command to the background instead
# of killing it, so only this surfaces a hang (exit 124). Under xvfb-run the
# timeout goes inside it, round the Python run: xvfb-run has no trap, so one
# killed from outside leaves its /tmp/xvfb-run.XXXXXX behind (20 there on
# 2026-11-17), while one whose command returns 124 cleans up. A second,
# longer timeout outside it catches an xvfb-run that never starts its command.

set -u

case "$0" in */*) . "${0%/*}/paths.sh" ;; *) . ./paths.sh ;; esac
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

case "$tree" in /*) ;; *) tree=$REPO/$tree ;; esac         # --tree may be relative to the checkout
logs=$SCRATCH
if [ -z "$export_rev" ]; then
    cd "$tree" || { echo "gates: cannot cd to $tree" >&2; exit 2; }
    tree=$PWD
    if [ "$tree" != "$REPO" ]; then
        name=${tree#"$REPO"/.claude/worktrees/}; name=${name#"$SCRATCH"/}; name=${name#/}
        logs=$SCRATCH/logs/${name//\//_}
        mkdir -p "$logs"
    fi
fi

if [ "$mode" = deprecations ]; then
    if [ ! -s "$logs/pytest.txt" ]; then
        echo "gates: no pytest log in $logs; run the suite first" >&2
        exit 2
    fi
    echo "deprecations reached by the last suite run ($(stat -c %y "$logs/pytest.txt" | cut -d. -f1)):"
    # A name is what follows DeprecationWarning or a subclass (PyGObject's
    # PyGIDeprecationWarning names its own API). PytestDeprecationWarning
    # is about pytest's configuration and names nothing: its "The" once
    # passed for a sixteenth name.
    grep -oE '[[:alnum:]_]*DeprecationWarning: [^[:space:]]+' "$logs/pytest.txt" \
        | grep -v '^PytestDeprecationWarning:' | sort -u
    exit 0
fi

if [ -n "$export_rev" ]; then
    sha=$(git -C "$REPO" rev-parse --short "$export_rev") || exit 2
    tree=$EXPORT_DIR/export-$sha
    rm -rf "$EXPORT_DIR"/export-*                    # one export at a time
    mkdir -p "$tree"
    git -C "$REPO" archive "$export_rev" | tar -x -C "$tree" || exit 2
    echo "export: $export_rev ($sha) unpacked at $tree"
    cd "$tree" || { echo "gates: cannot cd to $tree" >&2; exit 2; }
fi

mypy_cache=()
case "$tree" in "$SCRATCH"/*|"$EXPORT_DIR"/*) mypy_cache=(--cache-dir "$SCRATCH/mypy-cache") ;; esac

# Stamp for the Stop hook: the gates ran now, in this session, for this
# checkout; LOOP_NOTES must be newer by the end of the iteration. Reset the
# hook's block counter for this run.
printf '%s\t%s\n' "${CLAUDE_CODE_SESSION_ID:-}" "$REPO" > "$SCRATCH/gates.stamp"
rm -f "$SCRATCH/stop-blocks"

status=0

if [ "$mode" = all ] || [ "$mode" = pytest ]; then
    # The display: -a takes the first number without a lock file, so two runs
    # started together both take :99. One Xvfb dies, both suites share the
    # other, the first to finish takes it from under the second, and the run
    # whose Xvfb died ends in 1 whatever pytest returned (its `kill` fails under
    # set -e). -d lets Xvfb pick a free one itself; not every xvfb-run has it.
    display=-a
    xvfb-run --help 2>&1 | grep -q -- --auto-display && display=-d
    # The CI's screen: xvfb-run's own default is 640x480 here, and a window
    # is as large as the screen lets it be. The timeout goes inside xvfb-run,
    # round the Python run, so that xvfb-run cleans up after a hang; the outer
    # one is the backstop (see the head of this file).
    under_xvfb() {
        env -u WAYLAND_DISPLAY GDK_BACKEND=x11 timeout -k 5 $((T_PYTEST + 30)) \
            xvfb-run "$display" -s "-screen 0 1280x1024x24" timeout -k 5 "$T_PYTEST" "$@"
    }
    under_xvfb python3 -m pytest test/ -q -n "$WORKERS" > "$logs/pytest.txt" 2>&1
    rc=$?
    # Grep, never tail: the summary line is interleaved with warning output.
    summary=$(grep -E '[0-9]+ (passed|failed|error)' "$logs/pytest.txt" | tail -1)
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
        echo "pytest: HUNG, killed after ${T_PYTEST}s (a hang is a finding); last line: $(tail -1 "$logs/pytest.txt")"
        status=1
    elif [ "$rc" -ne 0 ] || [ -z "$summary" ]; then
        echo "pytest: FAILED (exit $rc): ${summary:-no summary line; see $logs/pytest.txt}"
        status=1
    else
        echo "pytest: $summary"
    fi

    # The test files this change touches - changed in the tree against HEAD,
    # or, in a clean tree, those HEAD changed; in an export, those the
    # exported revision changed - run twice more, where the CI differs from
    # this machine. Most tests that passed here and failed in the CI failed
    # under the oldest libraries MComix supports (the floors job: PyGObject
    # 3.46 cannot hand a render node to Python), or on a runner with four
    # processors, where a worker thread had not answered yet.
    #
    # At most GATE_CHUNK files go into one run, each run inside T_PYTEST: 33
    # window-test files were 76% through a single slow run when T_PYTEST killed
    # it, and nothing had hung. The floors chunks run one after another, under
    # SLOW_WORKERS workers, as the CI's floors job runs on its four processors.
    # The slow chunks run SLOW_RUNS times each, on two processors of their own,
    # as many at once as the machine has pairs. FLOORS_PYTHON is the floors
    # venv's interpreter. One chunk logs to floors.txt and slow.txt; more log
    # to floors-<n>.txt and slow-<n>.txt.
    if [ -n "$export_rev" ]; then
        touched=$(git -C "$REPO" diff --name-only "$export_rev~1" "$export_rev" -- 'test/test_*.py' 2>/dev/null)
    elif prefix=$(git rev-parse --show-prefix 2>/dev/null) && [ -z "$prefix" ]; then
        touched=$( { git diff --name-only HEAD -- 'test/test_*.py'
                     git ls-files --others --exclude-standard -- 'test/test_*.py'; } 2>/dev/null | sort -u)
        [ -n "$touched" ] || touched=$(git diff --name-only HEAD~1 HEAD -- 'test/test_*.py' 2>/dev/null)
    else
        touched=""
    fi
    files=()
    for f in $touched; do [ -f "$f" ] && files+=("$f"); done
    floors_python=${FLOORS_PYTHON:-$SCRATCH/floorsenv/bin/python}
    rm -f "$logs"/floors-*.txt "$logs"/slow-*.txt "$logs"/slow*.failed
    if [ ${#files[@]} -eq 0 ]; then
        echo "floors, slow: no test file touched"
    else
        per=${GATE_CHUNK:-8}
        workers=${SLOW_WORKERS:-4}
        runs=${SLOW_RUNS:-3}
        chunks=()                     # each a space-separated list of file names
        for ((i = 0; i < ${#files[@]}; i += per)); do chunks+=("${files[*]:i:per}"); done
        n=${#chunks[@]}
        chunk_log() { if [ "$n" -eq 1 ]; then echo "$logs/$1.txt"; else echo "$logs/$1-$2.txt"; fi; }
        count() { local m; m=$(grep -oE "[0-9]+ $1" <<< "$2" | head -1); m=${m%% *}; echo "${m:-0}"; }
        what="${#files[@]} files"; [ "$n" -gt 1 ] && what+=" in $n chunks"
        # Runs at once in one tree would race on .pytest_cache; none reads it.
        nocache=(-p no:cacheprovider)

        if [ -x "$floors_python" ]; then
            bad="" passed=0 skipped=0 last=""
            for ((c = 0; c < n; c++)); do
                log=$(chunk_log floors $((c + 1)))
                # shellcheck disable=SC2086  # a chunk is a list of file names
                under_xvfb "$floors_python" -m pytest ${chunks[c]} -q -rs -n "$workers" "${nocache[@]}" > "$log" 2>&1
                rc=$?
                last=$(grep -E '[0-9]+ (passed|failed|error|skipped)' "$log" | tail -1)
                if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
                    bad+="${bad:+; }HUNG, killed after ${T_PYTEST}s: $log"
                elif [ "$rc" -ne 0 ] || [ -z "$last" ]; then
                    bad+="${bad:+; }exit $rc: ${last:-no summary line}: $log"
                else
                    passed=$((passed + $(count passed "$last")))
                    skipped=$((skipped + $(count skipped "$last")))
                fi
            done
            if [ -n "$bad" ]; then
                echo "floors: FAILED ($what): $bad"; status=1
            elif [ "$n" -eq 1 ]; then
                echo "floors: $last (${files[*]})"
            else
                echo "floors: $passed passed, $skipped skipped ($what: ${files[*]})"
            fi
        else
            echo "floors: SKIPPED, no interpreter at $floors_python (STATE/scratch/floorsenv: technique \"A test that passes here and fails in the CI\")"
        fi

        pairs=$(( $(nproc) / 2 )); [ "$pairs" -ge 1 ] || pairs=1
        slow_chunk() {   # <log> <processors> <files>: up to $runs runs; a failed one stays in the log
            local run rc
            for run in $(seq "$runs"); do
                # shellcheck disable=SC2086  # a list of file names
                under_xvfb taskset -c "$2" python3 -m pytest $3 -q -n "$workers" "${nocache[@]}" > "$1" 2>&1
                rc=$?
                [ "$rc" -eq 0 ] || { echo "$run $rc" > "$1.failed"; return 1; }
            done
        }
        pids=()
        for ((c = 0; c < n; c++)); do
            [ "$c" -ge "$pairs" ] && wait "${pids[c - pairs]}"
            slot=$((c % pairs))
            cpus=$((2 * slot))-$((2 * slot + 1)); [ "$(nproc)" -ge 2 ] || cpus=0
            slow_chunk "$(chunk_log slow $((c + 1)))" "$cpus" "${chunks[c]}" &
            pids+=($!)
        done
        wait
        bad="" passed=0 last=""
        for ((c = 0; c < n; c++)); do
            log=$(chunk_log slow $((c + 1)))
            last=$(grep -E '[0-9]+ (passed|failed|error)' "$log" | tail -1)
            if [ -e "$log.failed" ]; then
                read -r run rc < "$log.failed"
                case "$rc" in
                    124|137) bad+="${bad:+; }HUNG in run $run of $runs, killed after ${T_PYTEST}s: $log" ;;
                    *) bad+="${bad:+; }run $run of $runs, exit $rc: ${last:-no summary line}: $log" ;;
                esac
            else
                passed=$((passed + $(count passed "$last")))
            fi
        done
        if [ -n "$bad" ]; then
            echo "slow: FAILED ($what): $bad"; status=1
        elif [ "$n" -eq 1 ]; then
            echo "slow: $runs runs on two processors, each $last"
        else
            echo "slow: $runs runs of each chunk on two processors of its own, $passed passed in each round ($what)"
        fi
    fi
fi

if [ "$mode" = all ] || [ "$mode" = static ]; then
    # Independent of each other, so flake8 runs beside mypy. The suite runs
    # alone: beside them it would run slower, and nearer its timeout.
    timeout -k 5 "$T_FLAKE8" python3 -m flake8 --select=F mcomix/ test/ \
        > "$logs/flake8.txt" 2>&1 &
    flake8_pid=$!
    timeout -k 5 "$T_MYPY" python3 -m mypy ${mypy_cache[@]+"${mypy_cache[@]}"} mcomix > "$logs/mypy.txt" 2>&1
    mypy_rc=$?
    wait "$flake8_pid"
    rc=$?
    if [ "$rc" -eq 124 ]; then
        echo "flake8: HUNG, killed after ${T_FLAKE8}s"; status=1
    elif [ "$rc" -ne 0 ] || [ -s "$logs/flake8.txt" ]; then
        echo "flake8: $(wc -l < "$logs/flake8.txt") lines (exit $rc); first: $(head -1 "$logs/flake8.txt")"
        status=1
    else
        echo "flake8: silent"
    fi

    rc=$mypy_rc
    if [ "$rc" -eq 124 ]; then
        echo "mypy: HUNG, killed after ${T_MYPY}s"; status=1
    elif [ "$rc" -ne 0 ]; then
        echo "mypy: FAILED (exit $rc): $(tail -1 "$logs/mypy.txt")"
        status=1
    else
        echo "mypy: $(tail -1 "$logs/mypy.txt")"
    fi
fi

# An export lies inside the skill's own repository when the skill is a git
# clone: name the revision exported, never the HEAD git finds above it.
if [ -n "$export_rev" ]; then
    at="$export_rev ($sha), exported"
elif prefix=$(git rev-parse --show-prefix 2>/dev/null) && [ -z "$prefix" ]; then
    at=$(git rev-parse --short HEAD)
else
    at="no checkout of its own"
fi
echo "tree: $tree at $at; logs: $logs"
exit $status
