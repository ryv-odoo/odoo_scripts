import psycopg2

from misc import psql_analyse, psql_explain_analyse, psql_vacuum_analyse, timed_call, OrderedSet

CONNECTION_PARAMS = "dbname=master"
TABLE = 'test_aggregate'

with psycopg2.connect(CONNECTION_PARAMS) as con:
    with con.cursor() as cur:
        cur.execute("SET jit_above_cost = -1")
        cur.execute("DROP TABLE IF EXISTS test_aggregate")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS test_aggregate (
            id SERIAL PRIMARY KEY,
            one_selection VARCHAR,
            one_int INTEGER,
            one_double double precision,
            one_decimal decimal
        )
        """)

def create_rows(nb):
    with psycopg2.connect(CONNECTION_PARAMS) as con, con.cursor() as cur:
        cur.execute("""
        INSERT INTO test_aggregate (one_selection, one_int, one_double, one_decimal)
        SELECT
            left(md5(s::text), 1),
            (random() * 1000000)::integer,
            random(),
            random()
        FROM generate_series(1, %s) AS s
        """, [nb])

queries_to_test = {
    # 'array_agg': 'SELECT array_agg("%(field)s") FROM test_aggregate',
    # 'array_agg distinct': 'SELECT array_agg(distinct "%(field)s") FROM test_aggregate',
    'array_agg order': 'SELECT array_agg("%(field)s" ORDER BY "%(field)s") FROM test_aggregate',
    'array_agg distinct order': 'SELECT array_agg(distinct "%(field)s" ORDER BY "%(field)s") FROM test_aggregate',
    # 'select': 'SELECT "%(field)s" FROM test_aggregate',
    # 'select distinct': 'SELECT DISTINCT "%(field)s" FROM test_aggregate',
    # 'select groupby': 'SELECT "%(field)s" FROM test_aggregate GROUP BY "%(field)s"',
    'select order': 'SELECT "%(field)s" FROM test_aggregate ORDER BY "%(field)s"',
    'select distinct order': 'SELECT DISTINCT "%(field)s" FROM test_aggregate ORDER BY "%(field)s"',
    'select groupby order': 'SELECT "%(field)s" FROM test_aggregate GROUP BY "%(field)s" ORDER BY "%(field)s"',
}

def one_test_explain(name, query, field):
    with psycopg2.connect(CONNECTION_PARAMS) as con, con.cursor() as cur:
        print(psql_explain_analyse(cur, query % {'field': field}))


def one_test(name, query, field):
    with psycopg2.connect(CONNECTION_PARAMS) as con, con.cursor() as cur:
        cur.execute(query % {'field': field})
        if 'array_agg' in name:
            results = tuple(cur.fetchone()[0])
        else:
            results = tuple(a for [a] in cur.fetchall())

        if 'distinct' in name or 'groupby' in name:
            return results
        return tuple(OrderedSet(results))

create_rows(1000000)
psql_vacuum_analyse(CONNECTION_PARAMS, TABLE)

for field in ['one_int', 'one_selection']:
    res = None
    for name, query in queries_to_test.items():
        print(f"\n\nFor {name} : \n")
        new_res, delta_ms = timed_call(one_test_explain, name, query, field, print_res=False)
        if res:
            assert new_res == res, f'{name} {len(new_res)} vs {len(res)}: {new_res} vs {res}'
        res = new_res


for field in ['one_int', 'one_selection']:
    print(f"\nFor {field} : ")
    for name, query in queries_to_test.items():
        new_res, delta_ms = timed_call(one_test, name, query, field, print_res=False)
        print(f"\t- {name} : {delta_ms:.4f} ms")


