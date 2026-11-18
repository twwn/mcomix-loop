#!/bin/sh
# Run pytest under Wine with MSYS2's UCRT64 Python: wine_pytest.sh <pytest args...>
# It runs in STATE/scratch/wine/tree, an export of the checkout, with the
# MSYS2 tree wine_windows_build.sh unpacks (scratch/wine/msys/root) and the
# pure-Python test packages in scratch/wine/pylib. MCOMIX_STATE_DIR
# overrides STATE.
#
# Run it as it is, not under xvfb-run: it starts an X server of its own.
# It keeps its own time and cleans up whatever ends it, so an outer
# `timeout` is a safety net only.
#
# A Wine start used to hang while libgtk-4-1.dll loaded (6 in 20 one hour,
# 1 in 10 another; Wine 11.22 staging, 2026-11-18): the main thread stopped
# inside wined3d.dll's process attach holding the loader lock, while GIO's
# Windows app-info thread waited for it. The plugin wine_started.py, loaded
# with -p before any conftest, asks GIO for every app first, which waits for
# that thread: 0 hangs in 50 starts. As a backstop, a run that has not
# finished collecting within WINE_START_TIMEOUT (45 s; a start, even one
# collecting all 5115 tests, takes about 9) is killed and started again, up
# to twice; the plugin says when collection is done.

STATE=${MCOMIX_STATE_DIR:-$(cd "$(dirname "$0")/.." && pwd)}
W=$STATE/scratch/wine
T=${WINE_RUN_TIMEOUT:-300}
START_T=${WINE_START_TIMEOUT:-45}

# Wine maps / to Z:, so a Windows path needs no wine process to work out.
winpath() { printf 'Z:%s' "$1" | tr / '\\'; }

export WINEPREFIX="$W/wineprefix"
export WINEDEBUG=-all
export GSK_RENDERER=cairo
export WINEPATH="$(winpath "$W/msys/root/ucrt64/bin")"
export PYTHONPATH="$(winpath "$W/pylib")"
export PYTHONDONTWRITEBYTECODE=1
# Unbuffered: a run killed by timeout otherwise loses everything pytest
# printed, and a hang before the first test looks like one inside it.
export PYTHONUNBUFFERED=1

cp "$STATE/probes/wine_started.py" "$W/pylib/wine_started.py" || exit 2
cd "$W/tree" || exit 2
unset GDK_BACKEND
# On a display of its own: Wine draws on whatever DISPLAY names, and a
# test that shows a window showed it on the user's screen (2026-11-15).
unset WAYLAND_DISPLAY

LOG=$W/wine_pytest.$$.log
DFILE=$W/wine_pytest.$$.display
MARK='wine_pytest: collected'
xvfb_pid=
run_pid=
status=1

# A wineserver left by an earlier run stays bound to that run's X server,
# which is gone, and the next wine hangs on it before its first line
# ("X connection to :2 broken"). Kill it and wait until it is gone.
stop_wine() { wineserver -k 2>/dev/null; timeout -k 2 20 wineserver -w 2>/dev/null; }

stop_x() {
	if [ -n "$xvfb_pid" ]; then
		kill "$xvfb_pid" 2>/dev/null
		wait "$xvfb_pid" 2>/dev/null
		xvfb_pid=
	fi
}

# Xvfb itself rather than xvfb-run: xvfb-run has no trap, so a kill left
# its Xvfb, and the wine under it, running. -displayfd picks a free display
# and writes its number once the server takes connections.
start_x() {
	: > "$DFILE"
	Xvfb -displayfd 1 -screen 0 1280x1024x24 -nolisten tcp \
		> "$DFILE" 2>/dev/null &
	xvfb_pid=$!
	n=0
	while [ ! -s "$DFILE" ] && [ $n -lt 100 ]; do
		sleep 0.1
		n=$((n + 1))
	done
	if [ ! -s "$DFILE" ]; then
		echo "wine_pytest.sh: Xvfb did not start" >&2
		return 1
	fi
	DISPLAY=:$(head -n 1 "$DFILE")
	export DISPLAY
}

# The run goes to a log, in the background, so that a signal to this
# script is answered at once (sh runs a trap only after the foreground
# command ends, and that command was the hang), and so that the start can
# be watched. Sets status; 125 means it never finished collecting.
run_once() {
	stop_wine
	start_x || { status=1; return; }
	timeout -k 5 "$T" wine "$W/msys/root/ucrt64/bin/python3.exe" -m pytest \
		-p no:cacheprovider -p wine_started \
		-o faulthandler_timeout="${WINE_TEST_TIMEOUT:-45}" "$@" \
		> "$LOG" 2>&1 &
	run_pid=$!
	waited=0
	hung=
	while kill -0 "$run_pid" 2>/dev/null && ! grep -q "$MARK" "$LOG"; do
		if [ $waited -ge "$START_T" ]; then
			hung=1
			kill "$run_pid" 2>/dev/null
			stop_wine
			break
		fi
		sleep 1
		waited=$((waited + 1))
	done
	wait "$run_pid"
	status=$?
	run_pid=
	# Only a start the watchdog cut off is tried again: one that ended
	# by itself before collecting (an import error) would end so again.
	[ -n "$hung" ] && status=125
	grep -v "$MARK" "$LOG"
	stop_wine
	stop_x
}

cleanup() {
	[ -n "$run_pid" ] && kill "$run_pid" 2>/dev/null
	stop_wine
	stop_x
	rm -f "$LOG" "$DFILE"
}
trap 'cleanup; exit 143' INT TERM HUP

started=$(date +%s)
tries=1
run_once "$@"
while [ $status -eq 125 ] && [ $tries -lt 3 ]; do
	echo "wine_pytest.sh: pytest did not finish collecting in ${START_T} s: Wine start-up hang, starting again" >&2
	tries=$((tries + 1))
	run_once "$@"
done
echo "wine_pytest.sh: exit $status after $(( $(date +%s) - started )) s, $tries start(s)" >&2
rm -f "$LOG" "$DFILE"
exit $status
