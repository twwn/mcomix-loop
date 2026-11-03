---
type: Ruling
title: Delete where the trash refuses the file
tags: [program]
generated: { by: mcomix-loop/audit, at: "2026-11-03T17:03:09Z" }
replaces: [2026-10-04-a-file-the-trash-refuses-is-offered-for, 2026-10-05-delete-asks-for-good-up-front-where-the-trash]
---

"Offer permanent delete (Recommended)" and "the deletion dialog ought to go straight for permanent deletion for files that will be refused (much like Nautilus also does)" (at 1a93048c and 273f3fe3) - where GLib is known to refuse the file, Delete (window) and remove-and-delete (library) ask the permanent-deletion question at once, never remembered, before anything is closed. A refusal not foreseen is answered afterwards with Cancel (the default) and a destructive "Delete Permanently". The trash button is suggested-action (blue), Delete Permanently destructive-action (red).
