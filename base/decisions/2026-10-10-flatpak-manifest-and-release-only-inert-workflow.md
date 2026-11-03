---
type: Ruling
title: "Flatpak manifest and release-only, inert workflow"
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-10-10T00:14:36Z" }
---

"flatpak-builder has been installed. Go with your proposal." and "The workflow should run only on tagged releases (i. e., \"26.10\" etc.) and, like for Chocolatey, not be actually live (yet) until credentials etc. have been set up." (at 71d0a044) - the loop writes the io.github.twwn.mcomix manifest, built and checked here with flatpak-builder, and a workflow that runs only on a pushed release tag and does nothing live until its credentials are set, as the Chocolatey publish job does.
