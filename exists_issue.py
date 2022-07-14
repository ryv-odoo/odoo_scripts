
import psycopg2

from misc import psql_analyse, psql_explain_analyse, psql_vacuum_analyse


# Bad alternative
# https://www.postgresql.org/message-id/CAApHDvpbJHwMZ1U-nzU0kBxu0kwMpBvyL%2BAFWvFAmurypSo1SQ%40mail.gmail.com

# cost estimation: https://www.postgresql.org/message-id/07b3fa88-aa4e-2e13-423d-8389eb1712cf%40imap.cc
# https://www.postgresql.org/message-id/flat/ff42b25b-ff03-27f8-ed11-b8255d658cd5@imap.cc


CONNECTION_PARAMS = "dbname=master"


with psycopg2.connect(CONNECTION_PARAMS) as con:
    con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)  # Vaccum need to be done outside transaction block
    with con.cursor() as cur:

        cur.execute("DROP TABLE IF EXISTS second_table")
        cur.execute("DROP TABLE IF EXISTS main_table")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS main_table (
            id SERIAL PRIMARY KEY,
            text VARCHAR
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS second_table (
            id SERIAL PRIMARY KEY,
            main_table_id INT REFERENCES main_table(id),
            time real
        )
        """)
        print("Insert in the first table")
        cur.execute("""
        INSERT INTO main_table (text)
        SELECT md5(random()::text)
        FROM generate_series(1, 100000) as s
        """)
        print("Insert in the second table")
        cur.execute("""
        INSERT INTO second_table (main_table_id, time)
        SELECT ceil(1 + random() * 99999), random() * 10000
        FROM generate_series(1, 250000) AS serie
        """)
        cur.execute("CREATE INDEX blable ON second_table(time)")
        cur.execute("CREATE INDEX blable1 ON second_table(main_table_id)")

        print("ANALYSE main_table")
        psql_analyse(CONNECTION_PARAMS, 'main_table')
        print("ANALYSE second_table")
        psql_analyse(CONNECTION_PARAMS, 'second_table')

        query = """
        SELECT COUNT(*) FROM main_table
        WHERE
            EXISTS (SELECT FROM second_table WHERE main_table.id = second_table.main_table_id AND time > 9995)
            OR
            NOT EXISTS (SELECT FROM second_table WHERE main_table.id = second_table.main_table_id AND time < 2000)
        """
        print("WITHOUT JIT")
        cur.execute("SET jit_above_cost = -1;")
        print(psql_explain_analyse(cur, query))
        print("WITH JIT")
        cur.execute("SET jit_above_cost = 500000;")
        print(psql_explain_analyse(cur, query))


        cur.execute(query)
        print(cur.fetchone()[0])
