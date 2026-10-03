---
type: Technique
title: "Upstream SourceForge tickets: reading them"
tags: [text]
sources:
  - { resource: "repo:README.md" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-03T00:55:09Z" }
---

- **The HTML pages answer curl with 403 (Cloudflare); the REST API does not.** `https://sourceforge.net/rest/p/mcomix/<tracker>/?limit=500` lists a tracker (bugs, feature-requests, patches, support-requests) as `tickets: [{ticket_num, summary}]`; `.../<tracker>/<n>/` gives `ticket` with status, created_date, description, labels and `discussion_thread.posts`. The forum is `.../discussion/1199430/?limit=500` (`forum.topics`, each with its own REST `url`; a topic's JSON is not keyed "thread" - print its keys first).
- **All 412 items fetch in a few minutes** with urllib, one request at a time, three tries each; at 2026-10-03: bugs 161 (26 open), feature requests 134 (71 open), patches 60 (7 open), support requests 28 (14 open), forum 29 topics.
- **Check a ticket against the tree, not against its age**: of the 26 open bugs, ten were already gone here (GTK 4 rewrites, fork fixes), two were still present (icon sizes 159, keybindings file 155), and one (145) was the fork's documented behaviour, which is a feature question, not a bug.
