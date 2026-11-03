"""Check that methods split out of the page_is_available() branch of MainWindow._draw_image are moved unchanged.

Usage, from REPO: timeout -k 5 60 python3 <this> <old rev> <method> [<method> ...]
The methods' bodies after their docstrings, concatenated in the order given, must be a run of
statements of the old branch, replaced in the new branch by one call each; everything else in
_draw_image must be unchanged.
"""
import ast
import subprocess
import sys

rev, names = sys.argv[1], sys.argv[2:]
old = subprocess.run(['git', 'show', f'{rev}:mcomix/main.py'], capture_output=True, text=True, check=True).stdout
new = open('mcomix/main.py').read()


def find(src, name):
    return [x for x in ast.walk(ast.parse(src)) if isinstance(x, ast.FunctionDef) and x.name == name][0]


def dump(xs):
    return [ast.dump(x) for x in xs]


def branch(fn):
    return [s for s in fn.body if isinstance(s, ast.If) and 'page_is_available' in ast.unparse(s.test)][0]


o, n = find(old, '_draw_image'), find(new, '_draw_image')
oif, nif = branch(o), branch(n)
moved = sum((dump(find(new, name).body[1:]) for name in names), [])
ob, nb = dump(oif.body), dump(nif.body)
k = next(i for i in range(len(ob)) if ob[i:i + len(moved)] == moved)
c = len(names)
print('moved at', k, len(moved), 'stmts; rest same', ob[:k] + ob[k + len(moved):] == nb[:k] + nb[k + c:],
      '; calls:', ' | '.join(ast.unparse(s) for s in nif.body[k:k + c]))
print('outside the branch same', dump([s for s in o.body if s is not oif]) == dump([s for s in n.body if s is not nif]),
      '; else same', dump(oif.orelse) == dump(nif.orelse), '; lines', n.end_lineno - n.lineno + 1)
