---
type: Technique
title: "Windows refuses to move or replace an open file: /proc/self/fd shows it on Linux"
tags: [windows]
sources:
  - { resource: "repo:test/test_main_window.py" }
  - { resource: "repo:.github/workflows/windows-tests.yml" }
generated: { by: mcomix-loop/claude, at: "2026-09-26T20:29:36+02:00" }
---

Windows opens files without FILE_SHARE_DELETE (Python's open() and zipfile included), so a file this process holds open cannot be renamed, moved or replaced there: WinError 32 on a move, WinError 5 on os.replace() over it. Linux allows both, so the suite here never sees it. The first Windows CI run (windows-tests.yml, at 7d665a52) found it for "Move to" and for saving the book, because archive_extractor.Extractor keeps the archive open for as long as the book is.

The Linux-side test: wrap the call that moves or replaces (file_mover.shutil.move, archive_packer.os.replace) and, inside it, list the descriptors of /proc/self/fd whose (st_dev, st_ino) match the file. `_descriptors_on()` in test/test_main_window.py does it; skip the test where /proc/self/fd is missing. On the old code each test found one descriptor.

The fix pattern: FileHandler.release_archive() waits for every member and closes the extractor's archive; Extractor.close() sets _archive to None so the later close of the book does not close it twice. Anything new that moves, renames or writes over the open archive calls release_archive() first.

Other POSIX-only things the Windows run tripped over, to avoid in new tests: os.getuid() (absent; guard with sys.platform first, since skipIf evaluates at import and one AttributeError kills collection of the whole file), os.mkfifo(), chmod-based "unwritable directory" (Windows ignores mode bits on directories), surrogate-escaped file names. chmod(0)-then-os.access() tests skip themselves there already.
