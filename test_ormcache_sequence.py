import psycopg2
import timeit

FACTOR = 1

sequences = {
    'registry': 50,
    'default': 100_000,  # NB row of that type
    'assets': 100,
    'templates': 500,
    'routing': 100,
    'groups': 1_500,
}

with psycopg2.connect('dbname=master') as con:
    with con.cursor() as cr:
        print('Drop tables')
        # Version 1: one table by type of sequence
        for seq in sequences:
            cr.execute(
                f'''DROP TABLE IF EXISTS signaling_{seq}'''
            )

        # Version 2: one table for rule them all
        cr.execute('''DROP TABLE IF EXISTS signaling''')
        for seq in sequences:
            cr.execute(f'DROP SEQUENCE IF EXISTS seq_signaling_{seq}')


with psycopg2.connect('dbname=master') as con:
    with con.cursor() as cr:

        print('Create tables')
        # Version 1: one table by type of sequence
        for seq in sequences:
            cr.execute(
                f'''CREATE TABLE signaling_{seq} (
                    id SERIAL PRIMARY KEY,
                    create_datetime timestamp NOT NULL DEFAULT NOW()
                )'''
            )

        # Version 2: one table for rule them all
        cr.execute(
            '''CREATE TABLE signaling (
                key VARCHAR NOT NULL,
                seq_id INTEGER NOT NULL,
                create_datetime timestamp NOT NULL DEFAULT NOW(),
                PRIMARY KEY (key, seq_id)
            )'''
        )
        for seq in sequences:
            cr.execute(f'CREATE SEQUENCE seq_signaling_{seq}')

        # Fill all tables
        print('Fill tables')
        # Version 1: one table by type of sequence
        for seq, nb_row in sequences.items():
            cr.execute(f'INSERT INTO "signaling_{seq}" SELECT FROM generate_series(1, %s)', [nb_row * FACTOR])
        # Version 2: one table for rule them all
        for seq, nb_row in sequences.items():
            cr.execute(f'INSERT INTO signaling (key, seq_id) SELECT %s, nextval(%s) FROM generate_series(1, %s) n', [seq, f'seq_signaling_{seq}', nb_row * FACTOR])

    con.commit()

with psycopg2.connect('dbname=master') as con:
    with con.cursor() as cr:
        cr.execute('ANALYSE')

def solution_1(cr):
    subqueries = [
        f"(SELECT MAX(id) FROM signaling_{seq})"
        for seq in sequences
    ]
    cr.execute(f"""
        SELECT {','.join(subqueries)}
    """)
    return dict(zip(sequences, cr.fetchall()))

# loose indexscan doesn't exists in PostgreSQL then don't use group by key + max(seq_id) 
# https://wiki.postgresql.org/wiki/Loose_indexscan
def solution_2(cr):
    cr.execute(f"""
        SELECT key, (SELECT MAX(signaling.seq_id) FROM signaling WHERE signaling.key = keys.key)
        FROM (VALUES {','.join(['%s'] * len(sequences))}) AS keys (key)
    """, [(key,) for key in sequences])
    return dict(cr.fetchall())


print('Launch test')
with psycopg2.connect('dbname=master') as con:
    with con.cursor() as cr:
        print(solution_1(cr))
        print(solution_2(cr))

        subqueries = [
            f"(SELECT MAX(id) FROM signaling_{seq})"
            for seq in sequences
        ]
        print("SOL1:", cr.mogrify(f"SELECT {','.join(subqueries)}").decode())

        subqueries = [
            f"(SELECT MAX(id) FROM signaling_{seq})"
            for seq in sequences
        ]
        print("SOL2:", cr.mogrify(f"""
SELECT key, (SELECT MAX(signaling.seq_id) 
FROM signaling WHERE signaling.key = keys.key) FROM (VALUES {','.join(['%s'] * len(sequences))}) AS keys (key)
        """, [(key,) for key in sequences]).decode())

        print("TIME solution 1:")
        print(timeit.timeit('solution_1(cr)', globals={'cr': cr, 'solution_1': solution_1}, number=1000))

        print("TIME solution 2:")
        print(timeit.timeit('solution_2(cr)', globals={'cr': cr, 'solution_2': solution_2}, number=1000))


