MComix loop: the context was just compacted mid-iteration. The head of the
skill's SKILL.md is re-attached by the harness; its tail (Campaigns,
Reporting, Reference) is not. If the heading "# MComix maintenance loop" is
not in context, Read SKILL.md (state.sh printed the skill's state/ directory;
SKILL.md is one level up). For the facts and the user's rulings, Read
reference.md and state/project.md, and run `python3 <skill>/scripts/okf.py
rulings`; for a technique, Read state/techniques/<name>.md. Read SKILL.md from
"## Campaigns" if LOOP_NOTES has a campaign open. What this iteration found
before the compaction is in state/scratch/iteration.txt; do not re-run
state.sh. If that file says a sweep is open, Read sweep.md beside SKILL.md and
go on from `scripts/sweep.sh wait`. Before a new lead or a sweep, run
`scripts/state.sh usage`: at the reserve of the 5-hour or the 7-day window,
start nothing new, end the iteration and wake when it says.
