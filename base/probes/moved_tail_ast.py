"""Like moved_block_ast.py, for a method that returns nothing: its whole body after the docstring
must occur as a run in the old function, replaced there by the one statement that calls it.

Usage, from REPO: timeout -k 5 60 python3 <this> <old rev> <file> <old function> <new method>
"""
import ast
import subprocess
import sys

rev, path, outer, inner = sys.argv[1:5]
old = subprocess.run(['git', 'show', f'{rev}:{path}'], capture_output=True, text=True, check=True).stdout
new = open(path).read()


def find(src, name):
    return [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == name][0]


def dump(xs):
    return [ast.dump(x) for x in xs]


oi, ni, m = find(old, outer), find(new, outer), find(new, inner)
moved, ob, nb = dump(m.body[1:]), dump(oi.body), dump(ni.body)
k = next(i for i in range(len(ob)) if ob[i:i + len(moved)] == moved)
print('moved at', k, len(moved), 'stmts; others same', ob[:k] + ob[k + len(moved):] == nb[:k] + nb[k + 1:], '; call:', ast.unparse(ni.body[k]))
