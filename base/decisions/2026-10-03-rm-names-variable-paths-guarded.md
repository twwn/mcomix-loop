---
type: Ruling
title: rm names variable paths guarded
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-10-03T10:10:58Z" }
---

"Consider it is a Dangerous rm operation on possibly-empty variable path: \"$U/$d\" in rm \"$U/$d\" (rewrite it as \"${U:?}/${d:?}\" or use a literal path)" (at 9eb48112, on the Wine prefix set-up) - an rm whose path comes from shell variables writes each as ${VAR:?}, so an empty one stops the command, or names the path literally.
