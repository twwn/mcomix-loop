---
type: Technique
title: "RAR archives a test builds by hand: names rar would refuse"
tags: [testing]
sources:
  - { resource: "repo:test/test_archives.py" }
  - { resource: "repo:mcomix/archive/rar.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-11-02T23:00:00Z" }
---

- **Only `unrar` is installed here, no `rar`, and `rar` would not write `../x` anyway.** `test/test_archives.py:_stored_rar(path, members)` writes a RAR 4 archive with stored members in about fifteen lines: the marker, a main block (0x73), per member a file block (0x74, flag 0x8000, method 0x30) followed by the data, and an end block (0x7b). Each block's first two bytes are the low 16 bits of the CRC32 of the rest of the block. Both libunrar 7.3.2 and `unrar` read it.
- **Every name it holds comes back exactly from the library's header**, which is what made `../../escaped.txt` testable: the library writes wherever `RARProcessFileW`'s DestName says, without looking at it. So anything joined to a destination has to be cleaned first (at d32e32d0).
- **A prefix without RAR readers**: the Wine prefix has none, so a test on real RAR behaviour needs the skip `_put_rar_set()` uses (`rar.RarArchive.is_available() or rar_external.RarArchive.is_available()`). Without a reader, the later volumes of a set are not later volumes as far as the library is concerned: it cannot list them, so they read as books that cannot be added.
- **The library overwrites too (probed at 15b71d17)**: a member named `../../victim.conf` replaced an existing file of that name, and `FileHandler._listed_contents` hands the extractor every listed member, pictures or not. The probe is the same hand-built RAR, a file placed where the name points, and `RarArchive.extract()`; run it with the tree under test first on `sys.path`.
