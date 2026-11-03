"""Check that a block of statements moved out of a function into a new method is unchanged.

Usage, from REPO: timeout -k 5 60 python3 <this> <old rev> <file> <old function> <new method>
The new method's body without its docstring and final return must occur as a run in the old
function's body; the old body minus that run must equal the new function's body except at the
one statement that now calls the method, which is printed old | new for reading.
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
moved = dump(m.body[1:-1])
ob, nb = dump(oi.body), dump(ni.body)
k = next(i for i in range(len(ob)) if ob[i:i + len(moved)] == moved)
rest = ob[:k] + ob[k + len(moved):]
print('moved at', k, len(moved), 'stmts; others same', rest[:k] + rest[k + 1:] == nb[:k] + nb[k + 1:])
print('old:', ast.unparse(oi.body[k + len(moved)]), '| new:', ast.unparse(ni.body[k]))
print('return:', ast.unparse(m.body[-1]))
