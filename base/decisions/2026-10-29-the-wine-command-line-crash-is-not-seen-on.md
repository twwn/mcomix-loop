---
type: Ruling
title: The Wine command-line crash is not seen on Windows
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-10-29T18:24:15Z" }
---

"I have been unable to observe the \"crash on Windows if file is given on the command-line\" issue" (at 0bdd950d, answering the question raised at 60b253cf) - on Windows, 26.10 opens a book given on the command line without the libgobject fault seen under Wine; the fault is treated as Wine's and is not pursued unless it shows on Windows.
