"""Mirror and inverse properties of MComix' pure geometry code.

Usage: python3 properties.py <mcomix tree>
Checks, over random values:
  - remap_axes() undone by inverse_axis_map(), and the inverse of an
    inverse being the order itself;
  - scroll_to_predefined() read backwards landing on the mirror of
    where it lands read forwards, for every destination code;
  - Box.intersect() and Box.bounding_box() being commutative, and each
    answer lying inside (or holding) what it was made from.
Prints one line per property with the number of mismatches.
"""
import itertools
import random
import sys

sys.path.insert(0, sys.argv[1])
from mcomix import constants, tools
from mcomix.box import Box
from mcomix.scrolling import Scrolling

random.seed(5)
DESTINATIONS = (0, 1, -1, constants.SCROLL_TO_CENTER,
                constants.SCROLL_TO_START, constants.SCROLL_TO_END)


def axis_maps():
    bad = 0
    for _ in range(20000):
        size = random.randint(1, 5)
        order = random.sample(range(size), size)
        vector = [random.randint(-50, 50) for _ in range(size)]
        back = tools.remap_axes(tools.remap_axes(vector, order),
                                tools.inverse_axis_map(order))
        twice = tools.inverse_axis_map(tools.inverse_axis_map(order))
        if back != vector or twice != list(order):
            bad += 1
    return bad


def scroll_to_predefined():
    scrolling = Scrolling()
    bad = 0
    for _ in range(20000):
        content = [random.randint(1, 400) for _ in range(2)]
        view = [random.randint(1, 300) for _ in range(2)]
        start = [random.randint(-100, 100) for _ in range(2)]
        position = [random.randint(-450, 450) for _ in range(2)]
        destination = [random.choice(DESTINATIONS) for _ in range(2)]
        content_box, viewport_box = Box(content, start), Box(view, position)
        forwards = scrolling.scroll_to_predefined(
            content_box, viewport_box, (1, 1), destination)
        # The mirror of a destination is the same code for the ones read
        # along the reading direction, and the opposite for the two that
        # name an end of the axis.
        mirrored_destination = [-d if d in (1, -1) else d
                                for d in destination]
        mirrored_position = [2 * s + c - v - p for s, c, v, p
                             in zip(start, content, view, position)]
        backwards = scrolling.scroll_to_predefined(
            content_box, Box(view, mirrored_position), (-1, -1),
            mirrored_destination)
        expected = [2 * s + c - v - f for s, c, v, f
                    in zip(start, content, view, forwards)]
        if backwards != expected:
            bad += 1
            if bad <= 3:
                print('  scroll_to_predefined', content, view, start,
                      position, destination, forwards, backwards, expected)
    return bad


def boxes():
    bad = 0
    for _ in range(20000):
        made = [Box([random.randint(1, 100) for _ in range(2)],
                    [random.randint(-50, 50) for _ in range(2)])
                for _ in range(2)]
        first, second = made
        if Box.intersect(first, second) != Box.intersect(second, first):
            bad += 1
            continue
        if Box.bounding_box(made) != Box.bounding_box(made[::-1]):
            bad += 1
            continue
        if Box.intersect(first, first) != first:
            bad += 1
            continue
        union = Box.bounding_box(made)
        for one in made:
            for axis in range(2):
                low = one.get_position()[axis]
                high = low + one.get_size()[axis]
                union_low = union.get_position()[axis]
                union_high = union_low + union.get_size()[axis]
                if low < union_low or high > union_high:
                    bad += 1
    return bad


for name, check in (('remap_axes/inverse_axis_map', axis_maps),
                    ('scroll_to_predefined mirror', scroll_to_predefined),
                    ('Box intersect/bounding_box', boxes)):
    print('%s: %d mismatches' % (name, check()))
