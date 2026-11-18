#!/bin/sh
# One python3.exe command under Wine, with wine_pytest.sh's set-up, on an
# Xvfb of its own, under WINE_RUN_TIMEOUT (30 s): wine_one.sh <python args>
STATE=${MCOMIX_STATE_DIR:-$(cd "$(dirname "$0")/.." && pwd)}
W=$STATE/scratch/wine
winpath() { printf 'Z:%s' "$1" | tr / '\\'; }
export WINEPREFIX="$W/wineprefix" WINEDEBUG=${WINEDEBUG:--all} GSK_RENDERER=cairo
export WINEPATH="$(winpath "$W/msys/root/ucrt64/bin")"
export PYTHONPATH="$(winpath "$W/pylib")" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
cd "$W/tree" || exit 2
unset GDK_BACKEND WAYLAND_DISPLAY
DF=$W/wine_one.$$.display
Xvfb -displayfd 1 -screen 0 1280x1024x24 -nolisten tcp > "$DF" 2>/dev/null &
X=$!
while [ ! -s "$DF" ]; do sleep 0.1; done
export DISPLAY=:$(head -n 1 "$DF")
trap 'wineserver -k 2>/dev/null; wineserver -w 2>/dev/null; kill $X 2>/dev/null; rm -f "$DF"' EXIT
trap 'exit 143' INT TERM HUP
timeout -k 5 "${WINE_RUN_TIMEOUT:-30}" wine "$W/msys/root/ucrt64/bin/python3.exe" "$@" &
p=$!
wait $p
echo "wine_one.sh: exit $?" >&2
