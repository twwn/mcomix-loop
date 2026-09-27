"""pytest plugin: record every SQL statement MComix' sqlite connections run.

Use: PYTHONPATH=<dir of this file> SQLTRACE_DIR=<dir> pytest ... -p sqltrace_plugin
Each process appends to <dir>/<pid>.sql, one statement per record,
separated by a line holding only ';;'.  STATE/probes/sql_plans.py then
explains every distinct statement.
"""
import os
import sqlite3

_connect = sqlite3.connect
_out = os.environ['SQLTRACE_DIR']


def _traced(*args, **kwargs):
    con = _connect(*args, **kwargs)
    path = os.path.join(_out, '%d.sql' % os.getpid())

    def record(statement):
        with open(path, 'a') as log:
            log.write(statement + '\n;;\n')

    con.set_trace_callback(record)
    return con


sqlite3.connect = _traced
sqlite3.dbapi2.connect = _traced
