---
type: Technique
title: "Encrypted archives: nothing asks on the reader's behalf"
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- `archive.password.never_asked()` is a thread-local context: every `BaseArchive._get_password()` on that thread answers '' without a prompt and does not remember it, and the yielded object's `.wanted` says whether any archive asked. The thumbnailer and `LibraryBackend.add_book()` run inside it; opening a book to read it does not. A handler may answer no password by raising (libunrar: "Couldn't open archive: Password missing" for EncryptedHeader.rar), so a caller inside it catches and checks `.wanted`.
- To test that nothing asks: patch `archive_password.ask_for_password` with a function that records the archive and calls `on_password(None)` at once - a mock that never answers hangs the test in `_get_password()`'s wait.
- Fixtures: Encrypted.{zip,rar,7z}, EncryptedHeader.{rar,7z} (listing encrypted too), SolidEncrypted*; password `password`.
