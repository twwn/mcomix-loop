#!/bin/sh
# Where a Wine test run's time goes: wineserver start, python3.exe start,
# importing gi and GTK, and pytest's start and collection, each timed on
# its own (wall seconds), on an Xvfb of its own. Same set-up as
# wine_pytest.sh; run it unwrapped, with an outer timeout.
STATE=${MCOMIX_STATE_DIR:-$(cd "$(dirname "$0")/.." && pwd)}
W=$STATE/scratch/wine
winpath() { printf 'Z:%s' "$1" | tr / '\\'; }
export WINEPREFIX="$W/wineprefix" WINEDEBUG=-all GSK_RENDERER=cairo
export WINEPATH="$(winpath "$W/msys/root/ucrt64/bin")"
export PYTHONPATH="$(winpath "$W/pylib")" PYTHONDONTWRITEBYTECODE=1
cd "$W/tree" || exit 2
unset GDK_BACKEND WAYLAND_DISPLAY
PY="$W/msys/root/ucrt64/bin/python3.exe"
DF=$W/wine_times.$$.display
Xvfb -displayfd 1 -screen 0 1280x1024x24 -nolisten tcp > "$DF" 2>/dev/null &
X=$!
while [ ! -s "$DF" ]; do sleep 0.1; done
export DISPLAY=:$(head -n 1 "$DF")
trap 'wineserver -k 2>/dev/null; kill $X 2>/dev/null; rm -f "$DF"' EXIT INT TERM
t() { label=$1; shift; s=$(date +%s.%N); "$@" > /dev/null 2>&1; e=$(date +%s.%N); echo "$label $(echo "$e - $s" | bc)"; }
wineserver -k 2>/dev/null; wineserver -w 2>/dev/null
t "cold: wine python -c pass" wine "$PY" -c pass
t "warm: wine python -c pass" wine "$PY" -c pass
t "warm: wine python -c pass" wine "$PY" -c pass
t "import gi + Gtk 4" wine "$PY" -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk"
t "import mcomix.main" wine "$PY" -c "import gi; gi.require_version('Gtk', '4.0'); import mcomix.main"
t "pytest --version" wine "$PY" -m pytest --version
t "pytest collect test_library_dialog.py" wine "$PY" -m pytest -p no:cacheprovider --collect-only -q test/test_library_dialog.py
t "pytest -k MissingBooksTest" wine "$PY" -m pytest -p no:cacheprovider -q -p no:warnings test/test_library_dialog.py -k MissingBooksTest
s=$(date +%s.%N); wineserver -k; wineserver -w; echo "wineserver -k and -w $(echo "$(date +%s.%N) - $s" | bc)"
