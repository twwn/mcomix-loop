#!/bin/sh
# Run pytest under Wine with MSYS2's UCRT64 Python: wine_pytest.sh <pytest args...>
# It runs in STATE/scratch/wine/tree, an export of the checkout, with the
# MSYS2 tree wine_windows_build.sh unpacks (scratch/wine/msys/root) and the
# pure-Python test packages in scratch/wine/pylib. MCOMIX_STATE_DIR
# overrides STATE.

STATE=${MCOMIX_STATE_DIR:-$(cd "$(dirname "$0")/.." && pwd)}
W=$STATE/scratch/wine

# Wine maps / to Z:, so a Windows path needs no wine process to work out.
winpath() { printf 'Z:%s' "$1" | tr / '\\'; }

export WINEPREFIX="$W/wineprefix"
export WINEDEBUG=-all
export GSK_RENDERER=cairo
export WINEPATH="$(winpath "$W/msys/root/ucrt64/bin")"
export PYTHONPATH="$(winpath "$W/pylib")"
export PYTHONDONTWRITEBYTECODE=1

cd "$W/tree" || exit 2
unset GDK_BACKEND
wineserver -k 2>/dev/null
wine "$W/msys/root/ucrt64/bin/python3.exe" -m pytest -p no:cacheprovider "$@"
status=$?
wineserver -k 2>/dev/null
exit $status
