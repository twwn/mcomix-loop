---
type: Ruling
title: GitHub Actions improvements; zizmor installed
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-10-30T16:33:57Z" }
---

"I've installed zizmor. Implement everything that makes sense. Also, while apparently the Windows test actions skip commits that don't make sense to test, the linux ones don't yet?" (at 75bb4e1a, on the loop's research of the workflows) - the loop implements the workflow improvements it judges sensible (RAR and LHA readers in the test jobs, skip reasons shown, pipefail, Flatpak cache, commit pins, smoke-test polling) and makes the Linux tests skip pushes that change nothing they test, keeping the manual's own checks; zizmor is installed here for auditing the workflows.
