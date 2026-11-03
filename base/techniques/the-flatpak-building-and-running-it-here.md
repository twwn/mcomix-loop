---
type: Technique
title: "The Flatpak: building it here, and running it in its sandbox"
tags: [testing]
sources:
  - { resource: "repo:flatpak/io.github.twwn.mcomix.yml" }
  - { resource: "repo:flatpak/flathub_manifest.py" }
  - { resource: "repo:.github/workflows/flatpak.yml" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-10T00:30:44Z" }
---

- (at 3387b223) **Building**: the GNOME 51 Platform and Sdk are installed in the user's Flatpak installation (a user remote "flathub" was added for them; the system one has no runtimes). `flatpak-builder --user --force-clean --state-dir=SCRATCH/fp-state SCRATCH/fp-build flatpak/io.github.twwn.mcomix.yml`; never --install (it would put the app in the user's menus). The first build took about seven minutes (7-Zip, DjVuLibre and Pillow compile); after that only the changed modules rebuild, a minute or two. Run it with `timeout -k 5 580` and the Bash timeout at 600000: a long build is resumed from the cache by running it again.
- **What broke on the way**: 7-Zip's makefile builds with -Werror, which GNOME 51's GCC stops on (array-bounds in ProgressUtils.h): CFLAGS_WARN_WALL="-Wall -Wextra". Pillow's sdist needs pybind11 to build. rename-appdata-file adds the old id as <provides><id>net.sourceforge.mcomix</id>, so the metainfo is rewritten by sed instead. libunrar has no soname, so ctypes.util.find_library misses it in the sandbox; rar.py tries /app/lib/libunrar.so.
- **Running a check inside**: `flatpak-builder --run <builddir> <manifest> python3 -c ...` sees only the sandbox, not the checkout. `flatpak build --filesystem=<dir>:ro <builddir> python3 -c ...` shares a folder; copy test archives into SCRATCH first. For the GUI, STATE/probes/flatpak_gui.py (argument: SCRATCH) starts `flatpak build --socket=x11 ... mcomix <book>` from a Python subprocess under xvfb-run with XDG_CONFIG_HOME, XDG_DATA_HOME, XDG_CACHE_HOME and HOME pointed into SCRATCH/fp-home, screenshots the root window and asks `xdotool search --class io.github.twwn.mcomix` for the window.
- **The Flathub copy**: `python3 flatpak/flathub_manifest.py <tag> <commit>` swaps the last module's dir source for the tag; building that copy from 26.09 (6db038e9) proved the git source path.
- (at 4e1310eb) **Build without --repo misses the export check**: flatpak build-export runs /usr/lib/flatpak-validate-icon on each exported icon and refuses one that is not square ("Expected a square icon but got: 3540x2655"), which stopped the 26.10 run on the CI. A build here proves the export only with `--repo=SCRATCH/fp-repo-test`; `flatpak build-export SCRATCH/fp-repo-test SCRATCH/fp-build` checks an existing build in seconds. Check one icon: `HOME=SCRATCH /usr/lib/flatpak-validate-icon --sandbox 512 512 <svg>`.
- (at 87992cad) **The bundle's artifact name**: flatpak/flatpak-github-actions/flatpak-builder@v6 names its artifact `<bundle without .flatpak>-<arch>.flatpak` unless `artifact-name` is given (index.js, artifactName); release.yml gives `flatpak`, so download-artifact puts the bundle at artifacts/flatpak/mcomix-<version>.flatpak. It builds the bundle with `--runtime-repo` set to Flathub's repository, so `flatpak install --user <bundle>` fetches the runtime. actionlint (gh release download --repo rhysd/actionlint --pattern '*linux_amd64.tar.gz', into scratch/actionlint) checks the workflows; 1.7.12 at 87992cad.
