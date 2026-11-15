#!/bin/sh
# start.sh <bundle dir> <out dir> <runs> : start MComix.exe under Wine <runs> times,
# each until its log says the status bar was measured; keep each log and the DLL load trace.
# On a display of its own: Wine draws on whatever DISPLAY names, and a
# window it opened came up on the user's screen (2026-11-15).
if [ -z "$WINE_PROBE_ON_XVFB" ]; then
	exec env -u WAYLAND_DISPLAY WINE_PROBE_ON_XVFB=1 xvfb-run -d -s "-screen 0 1280x1024x24" sh "$0" "$@"
fi
B=$1; O=$2; N=$3
# The prefix of the Wine build (technique "The Windows build"): state/scratch/winbuild2.
export WINEPREFIX="$(cd "$(dirname "$0")/.." && pwd)/scratch/winbuild2/wineprefix" GSK_RENDERER=cairo
unset WINEPATH GDK_BACKEND WAYLAND_DISPLAY
mkdir -p "$O"
wineserver -k 2>/dev/null
WINEDEBUG=-all wine cmd /c exit >/dev/null 2>&1   # wineserver up, not timed
i=1
while [ $i -le $N ]; do
  rm -f "$O/log$i.txt"
  WINEDEBUG=+loaddll wine "$B/MComix.exe" -W debug -o "$(winepath -w "$O/log$i.txt")" > "$O/out$i.txt" 2>&1 &
  n=0
  while [ $n -lt 400 ] && ! grep -aq "status bar is" "$O/log$i.txt" 2>/dev/null; do n=$((n+1)); python3 -c "import time; time.sleep(0.05)"; done
  WINEDEBUG=-all wine taskkill /f /im MComix.exe >/dev/null 2>&1
  wait
  i=$((i+1))
done
wineserver -k
