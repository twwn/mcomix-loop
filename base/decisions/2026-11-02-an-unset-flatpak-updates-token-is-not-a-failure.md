---
type: Ruling
title: An unset FLATPAK_UPDATES_TOKEN is not a failure
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-11-02T20:27:15Z" }
---

"Perhaps it also needs adjustment that \"FLATPAK_UPDATES_TOKEN is not set\" counts as failure, rather than quiet cancelation? (As flatpak is currently not yet ser up)" (at 742f81af, on the failed Flatpak updates run) - while the token is unset, newer releases of the Flatpak's modules do not fail flatpak-updates.yml: the run succeeds and says so in its summary and a notice.
