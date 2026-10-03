#!/bin/sh
# Run every test file on its own, uncaptured, eight at a time, each into
# its own log under STATE/scratch/perfile/. Run from the checkout, inside
# one xvfb-run.
[ -d test ] || { echo "perfile.sh: run it from the checkout" >&2; exit 2; }
OUT=$(cd "$(dirname "$0")/.." && pwd)/scratch/perfile
mkdir -p "$OUT"
ls test/test_*.py | xargs -P 8 -I{} sh -c \
    'timeout -k 5 55 python3 -m pytest "$1" -q -s -p no:cacheprovider > "$2/$(basename "$1").txt" 2>&1' _ {} "$OUT"
