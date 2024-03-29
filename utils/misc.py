
import itertools
import time

from typing import Iterable, Mapping, MutableSet
from statistics import fmean, pstdev, NormalDist

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
def remove_outliers(values, outlier_thr = 2):
    mean = fmean(values)
    std = pstdev(values)
    down_threeshold = (mean - outlier_thr * std)
    up_threeshold = (mean + outlier_thr * std)
    return list(filter(lambda v: v > down_threeshold and v < up_threeshold, values))

def statically_faster(values_1, values_2):
    """ Return true if values_1 is statically
    less (faster) than values_2
    """
    n1 = NormalDist.from_samples(values_1)
    n2 = NormalDist.from_samples(values_2)
    p = n1.overlap(n2)
    return p < 0.01 and fmean(values_1) < fmean(values_2)

def x_bests(values, x):
    return sorted(values)[:x]

def timed_call(method, *method_args, print_res=True, suffix=''):
    start = time.time_ns()
    res = method(*method_args)
    ms_delta = (time.time_ns() - start) / 1_000_000
    if print_res:
        print(f"'{method.__name__}' {suffix}: {ms_delta:.3f} ms")
    return res, ms_delta

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

class OrderedSet(MutableSet):
    """ A set collection that remembers the elements first insertion order. """
    __slots__ = ['_map']

    def __init__(self, elems=()):
        self._map = dict.fromkeys(elems)

    def __contains__(self, elem):
        return elem in self._map

    def __iter__(self):
        return iter(self._map)

    def __len__(self):
        return len(self._map)

    def add(self, elem):
        self._map[elem] = None

    def discard(self, elem):
        self._map.pop(elem, None)

    def update(self, elems):
        self._map.update(zip(elems, itertools.repeat(None)))

    def difference_update(self, elems):
        for elem in elems:
            self.discard(elem)

    def __repr__(self):
        return f'{type(self).__name__}({list(self)!r})'

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

def psql_analyse(CONNECTION_PARAMS, table_name):
    with psycopg2.connect(CONNECTION_PARAMS) as conn:
        # conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)  # Vaccum need to be done outside transaction block
        with conn.cursor() as cur:
            cur.execute(f"ANALYZE {table_name if table_name else ''}")

def psql_vacuum_analyse(CONNECTION_PARAMS, table_name):
    with psycopg2.connect(CONNECTION_PARAMS) as conn:
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)  # Vaccum need to be done outside transaction block
        with conn.cursor() as cur:
            cur.execute(f"VACUUM ANALYZE {table_name if table_name else ''}")

def psql_explain(cur, query):
    cur.execute("EXPLAIN " + query)
    return "\n".join(s for s, in cur.fetchall())

def psql_explain_analyse(cur, query):
    cur.execute("EXPLAIN ANALYZE " + query)
    return "\n".join(s for s, in cur.fetchall())

def psql_explain_complete_analyse(cur, query):
    cur.execute("EXPLAIN (ANALYZE, SETTINGS, VERBOSE) " + query)
    return "\n".join(s for s, in cur.fetchall())
