"""List every reach into another object's or module's private name.

An Attribute whose attr starts with one underscore and whose value is
not self, cls or super(), across mcomix/: name, count, first file:line.
Run from the checkout's root.
"""
import ast
import collections
import glob

found = collections.defaultdict(list)
for path in sorted(glob.glob('mcomix/**/*.py', recursive=True)):
    tree = ast.parse(open(path, encoding='utf-8').read())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        name = node.attr
        if not name.startswith('_') or name.startswith('__'):
            continue
        value = node.value
        if isinstance(value, ast.Name) and value.id in ('self', 'cls'):
            continue
        if isinstance(value, ast.Call) and getattr(value.func, 'id', '') == 'super':
            continue
        found[name].append('%s:%d' % (path, node.lineno))
for name, places in sorted(found.items(), key=lambda item: -len(item[1])):
    print('%3d %-32s %s' % (len(places), name, places[0]))
