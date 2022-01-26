import psycopg2

from misc import psql_activate_trigram, psql_activate_unaccent, psql_explain_analyse, psql_set_timeout, psql_vacuum_analyse, timed_call

CONNECTION_PARAMS = "dbname=master"

TABLE = "model_a"

def create_table(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
            DROP TABLE IF EXISTS {TABLE};
            CREATE TABLE IF NOT EXISTS {TABLE} (
                id SERIAL PRIMARY KEY,
                name TEXT
            );
            """)
    conn.commit()

def create_gin_index(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE INDEX {TABLE}_gin ON {TABLE} USING gin(name gin_trgm_ops);
        """)


def create_row(conn, todo):
    with conn.cursor() as cur:
        cur.execute(f"""
        INSERT INTO {TABLE} (name)
        SELECT
            'bla' || s::text
        FROM generate_series(1, {todo}) AS s
        """)
    conn.commit()

psql_activate_trigram(CONNECTION_PARAMS)
psql_activate_unaccent(CONNECTION_PARAMS)
psql_set_timeout(CONNECTION_PARAMS, 20)

with psycopg2.connect(CONNECTION_PARAMS) as conn:
    timed_call(create_table, conn)
    timed_call(create_row, conn, 1_000_000)

timed_call(psql_vacuum_analyse, CONNECTION_PARAMS, TABLE)


def tests(conn):
    with conn.cursor() as cur:
        print("Normal ilike:")
        query_normal = f"""
        SELECT id, name FROM {TABLE} WHERE name ILIKE '%bla25%'
        """
        psql_explain_analyse(cur, query_normal)  # warmup
        print(psql_explain_analyse(cur, query_normal))

        print("\nUnaccent ilike:")
        query_unaccent = f"""
        SELECT id, name FROM {TABLE} WHERE unaccent(name) ILIKE unaccent('%bla25%')
        """
        psql_explain_analyse(cur, query_unaccent)  # warmup
        print(psql_explain_analyse(cur, query_unaccent))

        print("\nUnaccent ilike:")
        query_unaccent = f"""
        SELECT id, name FROM {TABLE} WHERE unaccent(name) COALESCE unaccent('%bla25%')
        """
        psql_explain_analyse(cur, query_unaccent)  # warmup
        print(psql_explain_analyse(cur, query_unaccent))

print()
print("WITHOUT INDEX")
with psycopg2.connect(CONNECTION_PARAMS) as conn:
    timed_call(tests, conn, suffix='without index')

print()
with psycopg2.connect(CONNECTION_PARAMS) as conn:
    timed_call(create_gin_index, conn)
timed_call(psql_vacuum_analyse, CONNECTION_PARAMS, TABLE)

print()
print("WITH GIN INDEX")
with psycopg2.connect(CONNECTION_PARAMS) as conn:
    timed_call(tests, conn, suffix='with index')



# COALESCE("ir_translation"."value", "model"."field") ilike '%pattern%'

# ("ir_translation"."value" IS NOT NULL and "ir_translation"."value" ilike '%pattern%') OR ("ir_translation"."value" IS NULL and "model"."field" ilike '%pattern%')