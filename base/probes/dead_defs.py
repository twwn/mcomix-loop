"""Every function defined under mcomix/ whose name appears nowhere else.

Run from the checkout: python3 <this file>. Counts identifier tokens over
every tracked .py file (mcomix/, test/, win32/, top level), and prints the
definitions whose name occurs once, i.e. only where it is defined.
Dunder methods and GObject do_* virtual functions are skipped. A name built
at run time (bookmark_menu's getattr(self, '_%s_activated' % name)) is a
false positive: check getattr() calls with non-literal names before
removing anything.
"""
import ast
import os
import re
import subprocess

files = subprocess.run(['git', 'ls-files', '*.py'], capture_output=True,
                       text=True).stdout.split()
src = {f: open(f).read() for f in files if os.path.exists(f)}
words: dict[str, int] = {}
for text in src.values():
    for word in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', text):
        words[word] = words.get(word, 0) + 1
for path, text in sorted(src.items()):
    if not path.startswith('mcomix/'):
        continue
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if (name.startswith('__') and name.endswith('__')) \
                    or name.startswith('do_'):
                continue
            if words.get(name, 0) <= 1:
                print(f'{path}:{node.lineno} {name}')
