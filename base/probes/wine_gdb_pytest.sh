#!/bin/sh
# wine_pytest.sh under MSYS2's gdb.exe: a C backtrace at a crash. Usage as wine_pytest.sh;
# gdb joins the arguments into one, so pass several node ids as @<file> (pytest reads it).
STATE=${MCOMIX_STATE_DIR:-$(cd "$(dirname "$0")/.." && pwd)}
W=$STATE/scratch/wine
winpath() { printf 'Z:%s' "$1" | tr / '\\'; }
export WINEPREFIX="$W/wineprefix" WINEDEBUG=-all GSK_RENDERER=cairo PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export WINEPATH="$(winpath "$W/msys/root/ucrt64/bin")"
export PYTHONPATH="$(winpath "$W/pylib")"
cd "$W/tree" || exit 2
unset GDK_BACKEND
wineserver -k 2>/dev/null
wine "$W/msys/root/ucrt64/bin/gdb.exe" -batch -ex "set pagination off" -ex run -ex "bt 60" -ex "info sharedlibrary" --args "$(winpath "$W/msys/root/ucrt64/bin/python3.exe")" -m pytest -p no:cacheprovider "$@"
status=$?
wineserver -k 2>/dev/null
exit $status
