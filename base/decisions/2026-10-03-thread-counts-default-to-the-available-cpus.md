---
type: Ruling
title: Thread counts default to the available CPUs
tags: [program]
generated: { by: mcomix-loop/claude, at: "2026-10-03T16:56:10Z" }
---

"The \"Maximum number of concurrent {extraction,thumbnail} threads\" is currently caped at 16 each. I'm not sure where this ceiling comes from, review if it's sensible. Can this be made to have an optimal auto setting (by default)?" then "The benchmark must be machine-independent — just take the number of threads available (while not exhausting other ressources)?" (at b91ee04e) - both thread preferences get an automatic setting, the default, which uses the number of CPUs available to the process rather than a count tuned on one machine, kept within what the other resources (memory, processes) allow.
