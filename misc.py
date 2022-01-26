
import time

from typing import Iterable, Mapping

import psycopg2

# -------------- Helper Constants
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'
UNDERLINE = '\033[4m'
RESET = '\033[0m'

BOLD = "\033[1m"


# -------------- Helpers
def x_bests(values, x):
    return sorted(values)[:x]

def timed_call(method, *method_args, print_res=True, suffix=''):
    start = time.time_ns()
    method(*method_args)
    delta = (time.time_ns() - start) / 1_000_000
    if print_res:
        print(f"'{method.__name__}' {suffix}: {delta:.3f} ms")
    return delta

# -------------- Odoo method/class
def unique(it):
    """ "Uniquifier" for the provided iterable: will output each element of
    the iterable once.

    The iterable's elements must be hashahble.

    :param Iterable it:
    :rtype: Iterator
    """
    seen = set()
    for e in it:
        if e not in seen:
            seen.add(e)
            yield e

def freehash(arg):
    try:
        return hash(arg)
    except Exception:
        if isinstance(arg, Mapping):
            return hash(frozendict(arg))
        elif isinstance(arg, Iterable):
            return hash(frozenset(freehash(item) for item in arg))
        else:
            return id(arg)
class frozendict(dict):
    """ An implementation of an immutable dictionary. """
    __slots__ = ()

    def __delitem__(self, key):
        raise NotImplementedError("'__delitem__' not supported on frozendict")

    def __setitem__(self, key, val):
        raise NotImplementedError("'__setitem__' not supported on frozendict")

    def clear(self):
        raise NotImplementedError("'clear' not supported on frozendict")

    def pop(self, key, default=None):
        raise NotImplementedError("'pop' not supported on frozendict")

    def popitem(self):
        raise NotImplementedError("'popitem' not supported on frozendict")

    def setdefault(self, key, default=None):
        raise NotImplementedError("'setdefault' not supported on frozendict")

    def update(self, *args, **kwargs):
        raise NotImplementedError("'update' not supported on frozendict")

    def __hash__(self):
        return hash(frozenset((key, freehash(val)) for key, val in self.items()))

# -------------------- PostgreSQL helper
def psql_activate_trigram(CONNECTION_PARAMS):
    with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

def psql_activate_unaccent(CONNECTION_PARAMS):
    with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

def psql_set_timeout(CONNECTION_PARAMS, timeout=10):
    with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cur:
        cur.execute(f"ALTER ROLE odoo SET statement_timeout = '{timeout}s'")

def psql_vacuum_analyse(CONNECTION_PARAMS, table_name):
    with psycopg2.connect(CONNECTION_PARAMS) as conn:
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)  # Vaccum need to be done outside transaction block
        with conn.cursor() as cur:
            cur.execute(f"VACUUM ANALYZE {table_name}")

def psql_explain(cur, query):
    cur.execute("EXPLAIN ANALYZE " + query)
    return "\n".join(s for s, in cur.fetchall())

def psql_explain_analyse(cur, query):
    cur.execute("EXPLAIN ANALYZE " + query)
    return "\n".join(s for s, in cur.fetchall())
