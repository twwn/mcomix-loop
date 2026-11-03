---
type: Ruling
title: Flatpak application id io.github.twwn.mcomix
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-10-03T16:15:00Z" }
---

"FR 119: How about \"net.github.mcomix\" (assuming it's free)" then "Then go with io.github.twwn.mcomix" (at 1cb025d6, after Flathub's rule that a GitHub-hosted app takes io.github.<owner>.<app> ruled out net.github) - the Flatpak manifest for this fork uses the application id io.github.twwn.mcomix, which does not collide with upstream's net.sourceforge.mcomix on Flathub; the manifest and the metainfo it installs carry that id. Replaces, for the Flatpak only, project.md's statement that the Flatpak id stays net.sourceforge.mcomix.
