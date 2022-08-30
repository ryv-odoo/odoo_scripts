import psycopg2

from misc import psql_activate_trigram, psql_activate_unaccent, psql_explain_analyse, psql_set_timeout, psql_vacuum_analyse, timed_call

CONNECTION_PARAMS = "dbname=master"
UNACCENT_METHOD = 'unaccent'

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

def create_unaccent_method(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
            REPLACE FUNCTION {UNACCENT_METHOD}(text)
            RETURNS text LANGUAGE SQL IMMUTABLE PARALLEL SAFE STRICT AS
            $func$
            SELECT unaccent('public.unaccent', $1)
            $func$
        """)
    conn.commit()

def create_gin_index(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE INDEX {TABLE}_gin ON {TABLE} USING gin(name gin_trgm_ops);
        """)

def create_unaccent_gin_index(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE INDEX {TABLE}_gin_unaccent ON {TABLE} USING gin({UNACCENT_METHOD}(name) gin_trgm_ops);
        """)

def create_index(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE INDEX {TABLE}_index ON {TABLE} USING (name);
        """)


def create_row(conn, todo):
    with conn.cursor() as cur:
        cur.execute(f"""
        INSERT INTO {TABLE} (name)
        SELECT
            repeat(md5(s::text), 40)
        FROM generate_series(1, {todo}) AS s
        """)
    conn.commit()

psql_activate_trigram(CONNECTION_PARAMS)
psql_activate_unaccent(CONNECTION_PARAMS)
psql_set_timeout(CONNECTION_PARAMS, 60)

with psycopg2.connect(CONNECTION_PARAMS) as conn:
    create_unaccent_method(conn)
    timed_call(create_table, conn)
    timed_call(create_row, conn, 100_000)

timed_call(psql_vacuum_analyse, CONNECTION_PARAMS, TABLE)


# Odoo SH
"""
CREATE SCHEMA IF NOT EXISTS unaccent_schema;
CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA unaccent_schema;
CREATE OR REPLACE FUNCTION public.o_unaccent(text)
    RETURNS text AS
$func$
SELECT unaccent_schema.unaccent('unaccent_schema.unaccent', $1)
$func$ LANGUAGE sql IMMUTABLE;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA unaccent_schema TO public;
GRANT USAGE ON SCHEMA unaccent_schema TO public;
"""

def tests(conn):
    with conn.cursor() as cur:
        print("Normal ilike:")
        query_normal = f"""
        SELECT 1 FROM {TABLE} WHERE name ILIKE '%a8a6%'
        """
        psql_explain_analyse(cur, query_normal)  # warmup
        print(psql_explain_analyse(cur, query_normal))

        print("\nO_Unaccent ilike (Immutable):")
        query_unaccent = f"""
        SELECT 1 FROM {TABLE} WHERE o_unaccent(name) ILIKE o_unaccent('%a8a6%')
        """
        psql_explain_analyse(cur, query_unaccent)  # warmup
        print(psql_explain_analyse(cur, query_unaccent))

        print("\nUnaccent ilike:")
        query_unaccent = f"""
        SELECT 1 FROM {TABLE} WHERE public.unaccent(name) ILIKE public.unaccent('%a8a6%')
        """
        psql_explain_analyse(cur, query_unaccent)  # warmup
        print(psql_explain_analyse(cur, query_unaccent))

        print("\nUnaccent (odoo) ilike:")
        query_unaccent = f"""
        SELECT 1 FROM {TABLE} WHERE {UNACCENT_METHOD}(name) ILIKE {UNACCENT_METHOD}('%a8a6%')
        """
        psql_explain_analyse(cur, query_unaccent)  # warmup
        print(psql_explain_analyse(cur, query_unaccent))

print()
print("WITHOUT INDEX")
with psycopg2.connect(CONNECTION_PARAMS) as conn:
    tests(conn)

with psycopg2.connect(CONNECTION_PARAMS) as conn:
    timed_call(create_gin_index, conn)
timed_call(psql_vacuum_analyse, CONNECTION_PARAMS, TABLE)

print()
print("WITH GIN INDEX")
with psycopg2.connect(CONNECTION_PARAMS) as conn:
    tests(conn)

with psycopg2.connect(CONNECTION_PARAMS) as conn:
    timed_call(create_unaccent_gin_index, conn)
timed_call(psql_vacuum_analyse, CONNECTION_PARAMS, TABLE)

print()
print("WITH Unaccent GIN INDEX")
with psycopg2.connect(CONNECTION_PARAMS) as conn:
    tests(conn)
# COALESCE("ir_translation"."value", "model"."field") ilike '%pattern%'

# ("ir_translation"."value" IS NOT NULL and "ir_translation"."value" ilike '%pattern%') OR ("ir_translation"."value" IS NULL and "model"."field" ilike '%pattern%')