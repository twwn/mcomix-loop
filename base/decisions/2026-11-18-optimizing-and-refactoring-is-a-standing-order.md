---
type: Ruling
title: "Optimizing and refactoring is a standing order, paused after three fruitless attempts in a row"
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-11-18T15:56:24Z" }
---

"Continue treating it as standing order, but as with the iterations overall, pause once three attempts have not brought up new things to optimize/refactor." (2026-11-18, at e96eebda, on "once out of leads, I will release") - when no other lead can be worked, the loop goes on looking for things to optimize and refactor, the tests included, with no sweep; each look that finds nothing new to change counts, a commit resets the count, and after three such looks in a row the loop pauses: it runs the pre-release checks and stops with a notification so the user can order the release.
