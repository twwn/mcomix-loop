---
type: Ruling
title: "A release request first checks the loop's notes"
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-11-01T11:49:10Z" }
---

"Perhaps such \"still todo\" verification by you should run every time after I ask you to release" - when the user asks for a release, before the release commit: read STATE/notes.md (leads, questions, the CI line) and settle what touches the release - CI runs the notes wait on, open code-scanning alerts, the ChangeLog draft brought up to date with every commit since the last release - then report what is done and what is left, with blockers first.
