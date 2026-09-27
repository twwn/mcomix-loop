#!/bin/sh
# Run pytest under Wine with MSYS2's UCRT64 Python: pt.sh <pytest args...>

# Derive base directory (anpassbar)
STATE_ROOT="${MCOMIX_STATE_DIR:-$HOME/.claude/skills/mcomix-loop/state}"
W="$STATE_ROOT/scratch/wine"

# Extract username from $HOME for Wine paths
USERNAME=$(basename "$HOME")

export WINEPREFIX="$W/wineprefix"
export WINEDEBUG=-all
export GSK_RENDERER=cairo
export WINEPATH="Z:\\home\\$USERNAME\\.claude\\skills\\mcomix-loop\\state\\scratch\\wine\\msys\\root\\ucrt64\\bin"
export PYTHONPATH="Z:\\home\\$USERNAME\\.claude\\skills\\mcomix-loop\\state\\scratch\\wine\\pylib"
export PYTHONDONTWRITEBYTECODE=1

cd "$W/tree"
unset GDK_BACKEND
wineserver -k 2>/dev/null
wine "$W/msys/root/ucrt64/bin/python3.exe" -m pytest -p no:cacheprovider "$@"
status=$?
wineserver -k 2>/dev/null
exit $status
