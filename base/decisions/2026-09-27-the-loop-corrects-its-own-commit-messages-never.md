---
type: Ruling
title: "The loop corrects its own commit messages, never the commits"
tags: [installation]
generated: { by: claude.ai/claude-opus-5.5, at: "2026-09-27T12:00:00Z" }
---

"Consider allowing to rewrite commit messages (not the commits themselves) for its own mix-ups" - a message the loop got wrong is corrected in two ways only. Its own newest commit, while nothing is on top and nothing has pushed it: `git commit --amend --only -F <file>`, which keeps the tree. Any other: `git notes append -F <file> <commit>`, which leaves the commit alone; `git log` shows the note under the message, and the user folds it in when he next rewrites history by hand. (Before this the user fixed 58102b86's subject himself.)
