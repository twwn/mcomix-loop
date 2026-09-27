---
type: Technique
title: The shell is zsh
tags: [testing]
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- **The Bash tool runs zsh here**, not bash, and each of these once gave a wrong or silently skipped result:
  - an unquoted `$FILES` holding several paths stays one word, so `cp $FILES dest` gets one path that does not exist (a gate script once re-read an old log this way and reported a pass it had not run);
  - `echo ====` fails ("= not found", `=word` is a command-path expansion) and aborts a `&&` chain - use `echo --`;
  - a glob that matches nothing aborts the whole command ("no matches found"), including an unquoted `grep --include=*.py`, a pathspec like `'mcomix/**/*.py'` passed to git, and `rm dir/*` on an empty directory;
  - `modules` is read-only and `path` is tied to `PATH` - assigning either breaks the command or every later lookup;
  - zsh's `echo` turns `\t` in a Windows path (`Z:\tmp`) into a tab.
- **Anything with arrays, lists of paths or `set -e` logic goes in a `#!/bin/bash` script** under `STATE/probes/` or SCRATCH, run with `bash`; clear a log before the run that writes it, so a skipped run cannot be read as a result.
- `grep` here is ugrep with colour, and `git grep` colours into a pipe too: use Python or `git --no-pager grep --no-color` for output that is cut or grepped again.
