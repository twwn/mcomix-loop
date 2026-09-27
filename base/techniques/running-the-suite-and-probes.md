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
