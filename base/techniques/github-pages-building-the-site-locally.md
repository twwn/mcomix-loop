---
type: Technique
title: "GitHub Pages: building the site locally"
tags: [text]
sources:
  - { resource: "repo:.github/workflows/pages.yml" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-03T00:42:59Z" }
---

- **The github-pages gem builds what actions/jekyll-build-pages builds.** In the scratchpad: a Gemfile with `gem "github-pages", group: :jekyll_plugins` plus webrick, csv, base64, bigdecimal, logger (Ruby 3.4 no longer bundles them); `BUNDLE_PATH=<dir>/gems bundle install` (a few minutes, once). Build with `PAGES_REPO_NWO=twwn/mcomix BUNDLE_GEMFILE=... BUNDLE_PATH=... bundle exec github-pages build --source site --destination _site`.
- **Ruby 3.4 breaks jekyll-github-metadata 2.16.1**: "'@Jekyll::GitHubMetadata::EditLinkTag#parts' is not allowed as an instance variable name". In the local copy only, edit-link-tag.rb's memoize_conditionally: take the label's part after the last "#". GitHub's action runs an older Ruby and needs nothing.
- **Stage the site with the workflow's own step**: extract its `run:` with python and yaml (`yaml.safe_load`, the step named "The pages, and the files they link to"), run it in an archive of HEAD with BASE_PATH=/mcomix, then build. Check every internal href of _site against the files (strip /mcomix/, a trailing / means index.html).
- **GitHub's plugins**: jekyll-optional-front-matter skips README, LICENSE, COPYING, CONTRIBUTING and a few more by name - CONTRIBUTING.md is copied unrendered unless it has a front matter; jekyll-readme-index makes README.md a directory's index.html; jekyll-relative-links turns links to .md into links to .html, including ../ ones within the site. kramdown's GFM ids matched test_wiki's anchors() for every page (at 098becc5).
- **Jekyll prints GitHub's `> [!NOTE]` alert as text**; the workflow turns it into `> **Note:**`.
