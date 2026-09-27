"""Attributes of self that are assigned somewhere under mcomix/ and read
nowhere in the tree.

Run from the checkout: python3 <this file>. Collects every `self.<name>`
store per file, and counts every load of `.<name>` on any object, plus the
name as a string (getattr, hasattr, connect by name), across every tracked
.py file. Prints the stores with no load. A name read under another
object's attribute (`window.x`) counts as read, so this errs towards
silence; what it prints is worth reading.
"""
import ast
import os
import re
import subprocess

files = subprocess.run(['git', 'ls-files', '*.py'], capture_output=True,
                       text=True).stdout.split()
trees = {f: ast.parse(open(f).read()) for f in files if os.path.exists(f)}
loads: set[str] = set()
strings: set[str] = set()
for tree in trees.values():
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and not isinstance(node.ctx, ast.Store):
            loads.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.update(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', node.value))
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Attribute):
            loads.add(node.target.attr)
for path, tree in sorted(trees.items()):
    if not path.startswith('mcomix/'):
        continue
    seen = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store)
                and isinstance(node.value, ast.Name) and node.value.id == 'self'
                and node.attr not in loads and node.attr not in strings
                and node.attr not in seen):
            seen.add(node.attr)
            print(f'{path}:{node.lineno} self.{node.attr}')
