---
type: Technique
title: "Patching a dependency's version"
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- **`PIL.__version__` patched before `PIL.Image` is imported makes the import itself fail.** `PIL/Image.py` compares `__version__` with its C extension's on first import and raises ImportError on a mismatch.  A test of `run.setup_dependencies()` that patches the version then exits through the "no Pillow found" branch, and passes for the wrong reason - it did, on the unfixed code, until `import PIL.Image` moved to the test module's top. Run a version-check test alone (`-k`) on HEAD as well as fixed: in the full suite something else has usually imported the module already, which hides this.
