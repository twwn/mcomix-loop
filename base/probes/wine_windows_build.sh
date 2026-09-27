#!/bin/sh
# Build the Windows package of the checkout's HEAD under Wine, from
# MSYS2's UCRT64 packages, and start it on a PDF; see LOOP_TECHNIQUES
# "The Windows build under Wine". Usage: wine_windows_build.sh <workdir>
# (a scratch folder; ~1.8 GB). Run from the checkout. Needs wine, zstd,
# curl, xvfb-run, ImageMagick's import.
set -eu
W=$(realpath "$1"); mkdir -p "$W"
HERE=$(dirname "$(realpath "$0")")
export WINEPREFIX="$W/wineprefix" WINEDEBUG=-all GSK_RENDERER=cairo
PKGS="gtk4 adwaita-icon-theme libadwaita libjxl python python-gobject python-pillow python-pip python-pymupdf pyinstaller"
if [ ! -d "$W/msys/root/ucrt64" ]; then
  mkdir -p "$W/msys/pkgs" "$W/msys/root"
  curl -sfL -o "$W/msys/ucrt64.db" https://repo.msys2.org/mingw/ucrt64/ucrt64.db
  python3 "$HERE/msys2_resolve.py" "$W/msys/ucrt64.db" $(for p in $PKGS; do printf 'mingw-w64-ucrt-x86_64-%s ' $p; done) > "$W/msys/files.txt"
  (cd "$W/msys/pkgs" && xargs -P 8 -I{} sh -c 'test -s "{}" || curl -sfL -o "{}" "https://repo.msys2.org/mingw/ucrt64/{}"' < ../files.txt)
  for f in "$W"/msys/pkgs/*.pkg.tar.zst; do
    zstd -dcq "$f" | tar -x -C "$W/msys/root" --exclude='.PKGINFO' --exclude='.MTREE' --exclude='.BUILDINFO' --exclude='.INSTALL'
  done
  # What pacman would have recorded (the build reads it for licences).
  python3 - "$W/msys" <<'PY'
import io, os, subprocess, sys, tarfile
D = sys.argv[1]; local = os.path.join(D, 'root', 'var', 'lib', 'pacman', 'local')
for f in sorted(os.listdir(os.path.join(D, 'pkgs'))):
    tar = tarfile.open(fileobj=io.BytesIO(subprocess.run(['zstd', '-dcq', os.path.join(D, 'pkgs', f)], capture_output=True, check=True).stdout))
    info = dict(l.split(' = ', 1) for l in tar.extractfile('.PKGINFO').read().decode().splitlines() if ' = ' in l)
    names = [m.name + ('/' if m.isdir() else '') for m in tar.getmembers() if not m.name.startswith('.')]
    entry = os.path.join(local, '%s-%s' % (info['pkgname'], info['pkgver'])); os.makedirs(entry, exist_ok=True)
    open(os.path.join(entry, 'desc'), 'w').write('%%NAME%%\n%s\n\n%%VERSION%%\n%s\n' % (info['pkgname'], info['pkgver']))
    open(os.path.join(entry, 'files'), 'w').write('%FILES%\n' + ''.join(n + '\n' for n in sorted(names)) + '\n')
PY
  timeout -k 5 180 xvfb-run -a wineboot --init
  timeout -k 5 120 xvfb-run -a wine "$W/msys/root/ucrt64/bin/glib-compile-schemas.exe" "$(winepath -w "$W/msys/root/ucrt64/share/glib-2.0/schemas")"
fi
rm -rf "$W/src" && mkdir -p "$W/src" && git archive HEAD | tar -x -C "$W/src"
export WINEPATH="$(winepath -w "$W/msys/root/ucrt64/bin")"
(cd "$W/src" && timeout -k 10 1200 xvfb-run -a wine "$W/msys/root/ucrt64/bin/python3.exe" win32/build_pyinstaller.py > "$W/build.log" 2>&1)
unset WINEPATH  # the bundle has to stand on its own
ls -la "$W"/src/dist/mcomix-win64-*.zip
python3 -c "import pymupdf, sys; d = pymupdf.open(); [d.new_page().insert_text((72, 72), 'Page %d' % n, fontsize=48) for n in (1, 2)]; d.save(sys.argv[1])" "$W/smoke.pdf"
cat > "$W/run.sh" <<SH
#!/bin/sh
wine "$W/src/dist/MComix/MComix.exe" -W debug -o "$(winepath -w "$W/smoke.log")" "$(winepath -w "$W/smoke.pdf")" > "$W/smoke.out" 2>&1 &
sleep 40; import -window root "$W/smoke.png"; wineserver -k; sleep 1
SH
chmod +x "$W/run.sh"
timeout -k 5 90 xvfb-run -a -s "-screen 0 1280x900x24" "$W/run.sh"
grep -aE "Page 1 is available|Traceback|Uncaught" "$W/smoke.log" || true
echo "screenshot: $W/smoke.png"
