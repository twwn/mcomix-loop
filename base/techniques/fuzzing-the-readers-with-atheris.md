---
type: Technique
title: Fuzzing the readers with Atheris
tags: [testing]
sources:
  - { resource: "repo:fuzz/fuzz_ion.py" }
  - { resource: "repo:fuzz/fuzz_kfx.py" }
  - { resource: "repo:fuzz/fuzz_epub.py" }
  - { resource: "repo:fuzz/fuzz_comicinfo.py" }
  - { resource: "repo:.github/workflows/fuzz.yml" }
generated: { by: claude.ai/claude-opus-5.5, at: "2026-10-31T19:00:00Z" }
---

- (at 7dd354e6) **Running a target here**: `python3 -m venv --system-site-packages SCRATCH/fz` (the system Python 3.14 has gi; Atheris 3.1.0 has wheels for 3.12-3.14 only), `SCRATCH/fz/bin/python -m pip install --require-hashes -r .github/requirements/fuzz.txt`, then from a scratch folder `SCRATCH/fz/bin/python <checkout>/fuzz/fuzz_<t>.py <work dir> <checkout>/fuzz/corpus/<t> -max_total_time=300 -timeout=10 -rss_limit_mb=2048 -artifact_prefix=crash-<t>/`. No display is needed. Four in parallel (`&` and `wait`) fit the Bash tool's ten minutes at 360 s each. Replay an input: the target with the file as its only argument.
- **Seeds are not optional**: without fuzz/corpus/ the Ion target stays at coverage 2 - `bytes.startswith(VERSION_MARKER)` gives libFuzzer no comparison to learn from. `xvfb-run -a python3 fuzz/make_seeds.py` writes them from test/test_ion, test_kfx and test_epub's builders.
- **What it found, and the kinds to expect** (83bb5b0e, 96860b04, 4251e466): exceptions of other types than the reader's own - decimal's OverflowError/InvalidOperation in Ion; expat's ValueError for multi-byte declared encodings and LookupError for unknown ones; every way zipfile fails on a damaged directory or member (UnicodeDecodeError, NotImplementedError, RuntimeError, OSError, EOFError, zlib.error, LZMAError, ZstdError, BadZipFile - archive_base.ZIP_MEMBER_ERRORS); Pillow's SyntaxError/EOFError/struct.error besides OSError; offsets and lengths from the book's own data going to seek() and read() (OverflowError, MemoryError: read() allocates the length first). Each fix was replayed against every saved input, then the target ran again.
- **A target is replayed in the suite without Atheris**: test/test_fuzz_targets.py loads fuzz_<t>.py with stub `atheris` and `_setup` modules in sys.modules (removed afterwards; _setup would move HOME), so a target must change nothing at import - fuzz_kfx.py turns JPEG XR off only under `__main__`.
- (at 81d01317) **Six targets now** (ion, kfx, epub, mobi, comicinfo, sniff). A new one: write fuzz/fuzz_<t>.py as the others (import _setup, Atheris instrumenting `include=['mcomix']`, module-level work only under `__main__`), add its seeds to make_seeds.py (regenerating rewrites the KFX-ZIP seed's timestamps: restore it with `git checkout HEAD -- fuzz/corpus/kfx/kfx-zip`), add it to TARGETS and a test method in test/test_fuzz_targets.py, to fuzz.yml's matrix and paths, and to development.md. Commit the target before the fix it leads to, so the fix's commit holds the regression input and its test fails without the fix.
