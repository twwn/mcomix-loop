"""Explain every distinct statement sqltrace_plugin recorded.

Usage: python3 sql_plans.py <SQLTRACE_DIR>
Builds an in-memory database from the CREATE statements in the trace
(the first that runs cleanly for each object wins), then runs EXPLAIN
QUERY PLAN on every other distinct statement - literals folded, so one
statement asked with different values counts once - and prints those
whose plan scans a whole table, with how often the suite ran them.
"""
import collections
import glob
import os
import re
import sqlite3
import sys

records = []
for path in sorted(glob.glob(os.path.join(sys.argv[1], '*'))):
    with open(path) as trace:
        records += [r.strip() for r in trace.read().split('\n;;\n') if r.strip()]

LITERAL = re.compile(r"'(?:[^']|'')*'|\b\d+(?:\.\d+)?\b")


def shape(statement):
    return ' '.join(LITERAL.sub('?', statement).split())


con = sqlite3.connect(':memory:')
creates = [r for r in records if re.match(r'(?is)\s*create\s', r)]
for statement in creates:
    try:
        con.execute(statement)
    except sqlite3.Error:
        pass

counts = collections.Counter()
example = {}
for statement in records:
    if not re.match(r'(?is)\s*(select|update|delete|insert|with)\b', statement):
        continue
    key = shape(statement)
    counts[key] += 1
    example.setdefault(key, statement)

scans = []
unexplained = 0
for key, statement in example.items():
    try:
        plan = con.execute('explain query plan ' + statement).fetchall()
    except sqlite3.Error:
        unexplained += 1
        continue
    details = [row[-1] for row in plan]
    bad = [d for d in details if d.startswith('SCAN ')
           and 'CONSTANT ROW' not in d]
    if bad:
        scans.append((counts[key], key, details))

print('%d statements, %d distinct, %d not explainable here, %d that scan'
      % (len(records), len(example), unexplained, len(scans)))
for count, key, details in sorted(scans, reverse=True):
    print('\n%6d x %s' % (count, key[:300]))
    for detail in details:
        print('         ' + detail)
