---
type: Technique
title: "Package channels: what each accepts, and which credential it needs"
tags: [code]
sources:
  - { resource: "repo:.github/workflows/release.yml" }
  - { resource: "repo:.github/workflows/publish.yml" }
  - { resource: "repo:flatpak/flathub_manifest.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-18T21:30:00Z" }
---

Read from each channel's own documentation on 2026-10-18; re-read the page before relying on a rule, they change.

- **PyPI trusted publishing** (docs.pypi.org/trusted-publishers/troubleshooting): "Reusable workflows cannot currently be used as the workflow in a Trusted Publisher" (warehouse#11096). The upload job has to sit in the top-level workflow (release.yml), and the environment named on PyPI has to match the job's `environment:` exactly. No secret; `id-token: write` on the upload job only. PyPI never accepts a file name twice, so a release re-made from a moved tag cannot replace its PyPI files.
- **GitHub environment secrets in a reusable workflow**: the called workflow's job sets `environment:`; the caller cannot, and "must still pass the secret" by name, even one that exists only in the environment. An environment secret wins over a repository secret of the same name. Secrets cannot be read in a job-level `if:`; `vars` can.
- **winget-releaser**: classic PAT with `public_repo` ("New fine-grained PATs aren't supported"); `fork-user` names the account holding the winget-pkgs fork. A bot account limits what that scope reaches.
- **Flathub** (docs.flathub.org/docs/for-app-authors/requirements, maintenance): "Flathub manifests must not contain AI-generated or AI-assisted content. Disclosure does not exempt manifests from this restriction." AI agents must not open or automate submission pull requests or write their text; AI-generated application code must be disclosed, and reviewers may reject on its extent. Forks with minimal changes of an app already there are rejected. The loop therefore cannot write or draft the manifest submitted to Flathub, not even for the user to review; research and discussion with no generated material included is allowed. After acceptance Flathub's own external data checker runs every two hours and opens the update pull request from `x-checker-data`; no token of ours is needed.
- **SignPath Foundation** (signpath.org/terms): only artifacts built from the project's own source are signed (MComix.exe, the MSI); upstream binaries (MSYS2's DLLs, Python's .pyd) may ship unsigned but may not be signed. Every release needs manual approval in SignPath; all team members need MFA; the project's home page needs a "Code signing policy" section naming team roles and a privacy statement; the certificate's publisher is "SignPath Foundation". The GitHub action (`signpath/github-action-submit-signing-request`) takes `api-token`, `organization-id`, `project-slug`, `signing-policy-slug`, `artifact-configuration-slug` and `github-artifact-id` (the `artifact-id` output of actions/upload-artifact v4+); the uploaded zip is the artifact configuration's root `<zip-file>`, or `archive: false` with `skip-decompress: true` for a single file. All jobs before the request must run on GitHub-hosted runners.
