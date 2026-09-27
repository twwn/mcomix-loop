"""Random check that smart scrolling backwards mirrors it forwards.

Usage: python3 mirror_scroll.py <mcomix tree>
For 20,000 random pages, viewports, step sizes and viewport positions
(inside the page, before it and past it), scroll_smartly() read
backwards from the mirrored position must land on the mirror of where
it lands reading forwards.  Prints the first mismatches and a count.
"""
import random
import sys

sys.path.insert(0, sys.argv[1])
from mcomix.box import Box
from mcomix.scrolling import Scrolling

random.seed(3)
scrolling = Scrolling()
bad = 0
for _ in range(20000):
    content = [random.randint(1, 400) for _ in range(2)]
    view = [random.randint(1, 300) for _ in range(2)]
    steps = [random.choice([random.randint(1, 300), random.uniform(0.5, 300)])
             for _ in range(2)]
    pos = [random.randint(-450, 450) for _ in range(2)]
    forwards = scrolling.scroll_smartly(Box(content), Box(view, pos), (1, 1), steps)
    mirrored = [c - v - p for c, v, p in zip(content, view, pos)]
    backwards = scrolling.scroll_smartly(Box(content), Box(view, mirrored), (-1, -1), steps)
    expected = [] if forwards == [] else [c - v - x for c, v, x in zip(content, view, forwards)]
    if backwards != expected:
        bad += 1
        if bad <= 3:
            print('MISMATCH', content, view, steps, pos, forwards, backwards, expected)
print('mismatches', bad, 'of 20000')
