#!/bin/sh
# Run every test file on its own, uncaptured, eight at a time, each into
# its own log under perfile/. Meant to run inside one xvfb-run.
cd /tmp/mcomix-git || exit 2
mkdir -p /tmp/mcomix-loop-scratch/perfile
ls test/test_*.py | xargs -P 8 -I{} sh -c \
    'timeout -k 5 55 python3 -m pytest "$1" -q -s -p no:cacheprovider > "/tmp/mcomix-loop-scratch/perfile/$(basename "$1").txt" 2>&1' _ {}
