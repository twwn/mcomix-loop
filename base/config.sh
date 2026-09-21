# Copy to state/config.sh. Sourced by every script in scripts/; plain bash.
# The loop reads these and never edits this file.

WORKERS=8        # pytest-xdist workers. Measure: -n auto is slower on a suite this
                 # short because worker start-up dominates. 8 was the optimum on
                 # the author's machine.
T_PYTEST=60      # seconds, the suite and any probe; a hang is reported as HUNG
T_FLAKE8=60
T_MYPY=120

# Where `gates.sh --export` unpacks a clean tree (default: state/scratch/).
# On Python 3.12 and 3.13 the forkserver listens on a socket file whose path
# Linux caps at 108 bytes, and the suite puts its temporary files inside the
# tree, so an export under a long path fails every test that opens a PDF
# ("AF_UNIX path too long"). 3.14 uses abstract sockets and is not affected.
# EXPORT_DIR=/tmp/mcomix-loop

# Checkouts that other sessions own, as absolute paths. The guard refuses any
# command, Edit or Write that names one. Empty means none.
FOREIGN=()
# FOREIGN=(/home/me/src/mcomix-pr-prep)
