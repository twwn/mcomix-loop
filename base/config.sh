# Copy to state/config.sh. Sourced by every script in scripts/; plain bash.
# The loop reads these and never edits this file.

WORKERS=8        # pytest-xdist workers. Measure: -n auto is slower on a suite this
                 # short because worker start-up dominates. 8 was the optimum on
                 # the author's machine.
T_PYTEST=60      # seconds, the suite and any probe; a hang is reported as HUNG
T_FLAKE8=60
T_MYPY=120

# Where `gates.sh --export` unpacks a clean tree (default: state/scratch/).
# On Python 3.12, and 3.13 before 3.13.6, the forkserver listens on a socket file
# whose path Linux caps at 108 bytes, and the suite puts its temporary files
# inside the tree, so an export under a long path fails every test that opens a
# PDF ("AF_UNIX path too long"). From 3.13.6 on, 3.14 and 3.15 included, Python
# falls back to the system's temporary directory when the path would be too long.
# EXPORT_DIR=/tmp/mcomix-loop

# Checkouts that other sessions own, as absolute paths. The guard refuses any
# command, Edit or Write that names one. Empty means none.
FOREIGN=()
# FOREIGN=(/home/me/src/mcomix-pr-prep)

# Sweeps, when no lead can be worked (sweep.md). A lens that found nothing runs
# again after SWEEP_EVERY commits under mcomix/ or docs/; 0 means no sweeps.
# SWEEP_WIDTH is the number of auditors at once, each a whole subagent's tokens.
# SWEEP_MODEL (haiku, sonnet, opus, fable) and SWEEP_EFFORT (low, medium, high,
# xhigh, max) are what an auditor runs at. The main thread checks every lead
# itself, so a cheaper auditor's false leads come back as its own cost, and a lens
# that misses what is there rests. It may name another tier for a lens of one
# sweep, up to opus/high (sweep.md).
SWEEP_EVERY=25
SWEEP_WIDTH=5
SWEEP_MODEL=sonnet
SWEEP_EFFORT=high

# The only GitHub writes the guard lets through. ISSUES_REPO (owner/name):
# gh issue create, edit, comment, close and reopen, each with --repo naming
# it; state.sh reads its issues and discussions. ISSUES_PROJECT
# (owner/number, from the project's URL): gh project item-add, item-edit and
# field-create on it, as `<number> --owner <owner>`; the token needs the
# project scope (gh auth refresh -s project). Empty: none.
ISSUES_REPO=""
ISSUES_PROJECT=""
# ISSUES_REPO=me/mcomix
# ISSUES_PROJECT=me/1
