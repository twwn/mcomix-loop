---
type: Technique
title: Running the suite and probes
tags: [testing]
generated: { by: mcomix-loop/claude, at: "2026-09-26T15:13:41+02:00" }
---

- **Always under Xvfb**, and with X rather than Wayland: `env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -a ...`. A bare pytest run against no display hangs rather than failing.
- **`-n WORKERS` (`STATE/config.sh`; 8 on a 24-core machine) is the measured optimum** for the suite: 27 s for 3,620 tests at dc0c098f (nine seconds against thirty-three serial when it was a third of that size). `-n auto` fans out to every core and is slower: worker startup dominates a suite this short. `--dist loadfile` is the fallback if shared state starts biting.
- **Timeouts belong on every run.** 60 s for the suite and any probe, 120 s for mypy; the suite at 27 s has halved that margin since 16 s, so raise `T_PYTEST` in `STATE/config.sh` before it reaches ~45 s. A longer timeout hides a hang instead of surfacing one — which is how the `_BookArea` hang below was found.
- **Two sessions running gates.sh at once share SCRATCH/pytest.txt** (at a463e922): the log then holds two summaries and stray bytes, gates.sh's grep calls it a binary file and reports "no summary line". While another session is active, run the suite on the export by hand with its output in a log of your own name, and read the summary with `grep -a`.
- **A hand-written check for failures must not match "12 xfailed"**: grep for `(^| )[0-9]+ failed`.
- (at 00e6f348) **A suite that is killed at the timeout near 98 % is not always a hang: look at where its temporary files lie.** `test/__init__.py` keeps its temporary root in `<tree>/test/tmp`, so an export under STATE runs its SQLite tests on the disk, where each commit is an fsync: at 5.2 ms an fsync (50 writes timed with `os.fsync`; 0 ms on a tmpfs) UpgradeFromEveryVersionTest's 10 tests took 19.93 s from the export against 0.57 s in a checkout on /tmp, and the whole suite 72.77 s against 30 s, at 256 % CPU with eight workers. Tell the two apart with a longer timeout and `--durations=25`: a hang has no summary, a slow disk has one and lists the database tests first.
- (at 00e6f348) **pytest 9.2 prints `u` for a passed subtest** and counts "N subtests passed" in the summary; a progress line full of `u` is not a line of failures.
- (at 00e6f348) **A probe that needs a full disk mounts one in a user namespace**: `unshare -Urm sh -c 'mount -t tmpfs -o size=64k tmpfs "$0/full" && exec timeout -k 5 170 xvfb-run -d -s "-screen 0 1280x1024x24" python3 "$0/probe.py" "$0/full"' <dir>`. The guard wants the `timeout` directly before `xvfb-run`, inside the `sh -c`.
