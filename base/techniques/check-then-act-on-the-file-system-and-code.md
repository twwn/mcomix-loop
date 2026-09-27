---
type: Technique
title: "Check-then-act on the file system, and code loaded from the working directory"
tags: [code]
sources:
  - { resource: "repo:mcomix/archive/rar.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-24T07:45:21+02:00" }
---

- **MComix runs one process per window**, so "if not exists: makedirs" is a race between two MComix started together: run.py's did it for DATA_DIR and CONFIG_DIR, and the second process died of FileExistsError (a2bd05cd). `git grep -n "os.path.exists"` and read each one followed by a create; `os.makedirs(..., exist_ok=True)` and opening with the right mode are the answers. A test drives the race by making the directory first and patching os.path.exists to False.
- **Nothing is loaded from the current directory on Unix.** rar.py tried libunrar.so from os.getcwd() after the system's (22f242da). `git grep -n "getcwd"`: file_provider (a default for a relative path), process.find_executable (only for names with a directory part on Unix; Windows puts workdir first by its own convention) and openwith (the working directory of a command the reader typed) are deliberate. The test patches ctypes.util.find_library to None and ctypes.cdll.LoadLibrary to record and refuse, after clearing _get_unrar_dll's functools.cache.
