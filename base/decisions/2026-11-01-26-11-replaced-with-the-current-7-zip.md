---
type: Ruling
title: 26.11 replaced with the current 7-Zip
tags: [installation]
generated: { by: mcomix-loop/claude, at: "2026-11-01T12:16:13Z" }
---

"Go with 1." (at ac2e5e78) - 26.11 shipped 7-Zip 26.04 from the runner image while 26.05 (vulnerabilities fixed) was out; the build fetches 7-Zip from 7-zip.org as it fetches UnRAR, and 26.11 is replaced, not followed by 26.11.1: the tag moves to the fixed commit and the published release is deleted by hand, keeping the tag.
