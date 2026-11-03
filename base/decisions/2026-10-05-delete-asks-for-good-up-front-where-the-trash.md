---
type: Ruling
title: Delete asks for good up front where the trash refuses; Move to Trash is blue
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-10-05T14:55:41Z" }
---

"the deletion dialog ought to go straight for permanent deletion for files that will be refused (much like Nautilus also does), rather than offer the Trash dialog only to fail. (Or unify it into one dialog which updates itself accordingly, whatever is clearer.) Also, for visual difference, the \"Move to Trash\" button ought to be blue instead (\"Delete permanently\" remains red)." (at 273f3fe3) - where GLib is known to refuse the file, Delete (window) and remove-and-delete (library) ask the permanent-deletion question at once, never remembered, before anything is closed; the after-the-fact offer stays only for refusals not foreseen. The trash button is suggested-action (blue), Delete Permanently destructive-action (red).
