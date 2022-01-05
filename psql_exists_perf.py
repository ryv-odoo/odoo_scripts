from collections import defaultdict
import time
import pickle
from typing import NamedTuple
from statistics import fmean
import random
import itertools

import psycopg2
import psycopg2.extensions
import psycopg2.errors

from misc import unique

psql_version = ["9", "10", "11", "12", "13", "14"]

TIMEOUT_REQUEST = 10  # in sec
TABLE_1 = "model_a"
TABLE_2 = "model_b"
TABLE_MANY_2_MANY = f"{TABLE_1}_{TABLE_2}_rel"

def activate_extention(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
        CREATE EXTENSION IF NOT EXISTS "tablefunc";
        ALTER ROLE odoo SET statement_timeout = '{TIMEOUT_REQUEST}s';
        """)
    conn.commit()

def create_many_2_many(cur):
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS "{TABLE_MANY_2_MANY}" (
            "{TABLE_1}_id" INTEGER NOT NULL REFERENCES {TABLE_1}(id) ON DELETE CASCADE,
            "{TABLE_2}_id" INTEGER NOT NULL REFERENCES {TABLE_2}(id) ON DELETE CASCADE,
            PRIMARY KEY("{TABLE_1}_id", "{TABLE_2}_id")
        );
        CREATE INDEX ON "{TABLE_MANY_2_MANY}" ("{TABLE_2}_id", "{TABLE_1}_id");
    """)
    return f"{TABLE_MANY_2_MANY}"

def create_many_2_many_without_contraint(cur):
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS "{TABLE_MANY_2_MANY}" (
            "{TABLE_1}_id" INTEGER NOT NULL,
            "{TABLE_2}_id" INTEGER NOT NULL,
            PRIMARY KEY("{TABLE_1}_id", "{TABLE_2}_id")
        );
    """)
    return f"{TABLE_MANY_2_MANY}"

def create_many_2_many_contraint(cur, drop=False):
    if drop:
        cur.execute(f"""
        ALTER TABLE "{TABLE_MANY_2_MANY}" DROP CONSTRAINT IF EXISTS fk_{TABLE_MANY_2_MANY}_{TABLE_1}_id;
        ALTER TABLE "{TABLE_MANY_2_MANY}" DROP CONSTRAINT IF EXISTS fk_{TABLE_MANY_2_MANY}_{TABLE_2}_id;
        DROP INDEX IF EXISTS {TABLE_MANY_2_MANY}_inverse;
        """)
    else:
        cur.execute(f"""
            ALTER TABLE "{TABLE_MANY_2_MANY}" ADD CONSTRAINT fk_{TABLE_MANY_2_MANY}_{TABLE_1}_id
                FOREIGN KEY ({TABLE_1}_id) REFERENCES {TABLE_1} (id) ON DELETE CASCADE;
            ALTER TABLE "{TABLE_MANY_2_MANY}" ADD CONSTRAINT fk_{TABLE_MANY_2_MANY}_{TABLE_2}_id
                FOREIGN KEY ({TABLE_2}_id) REFERENCES {TABLE_2} (id) ON DELETE CASCADE;
            CREATE INDEX {TABLE_MANY_2_MANY}_inverse ON "{TABLE_MANY_2_MANY}" ("{TABLE_2}_id", "{TABLE_1}_id");
        """)

def create_many_2_many_contraint_v_13(cur, drop=False):
    if drop:
        cur.execute(f"""
        ALTER TABLE "{TABLE_MANY_2_MANY}" DROP CONSTRAINT IF EXISTS fk_{TABLE_MANY_2_MANY}_{TABLE_1}_id;
        ALTER TABLE "{TABLE_MANY_2_MANY}" DROP CONSTRAINT IF EXISTS fk_{TABLE_MANY_2_MANY}_{TABLE_2}_id;
        DROP INDEX IF EXISTS {TABLE_MANY_2_MANY}_a;
        DROP INDEX IF EXISTS {TABLE_MANY_2_MANY}_b;
        """)
    else:
        cur.execute(f"""
            ALTER TABLE "{TABLE_MANY_2_MANY}" ADD CONSTRAINT fk_{TABLE_MANY_2_MANY}_{TABLE_1}_id
                FOREIGN KEY ({TABLE_1}_id) REFERENCES {TABLE_1} (id) ON DELETE CASCADE;
            ALTER TABLE "{TABLE_MANY_2_MANY}" ADD CONSTRAINT fk_{TABLE_MANY_2_MANY}_{TABLE_2}_id
                FOREIGN KEY ({TABLE_2}_id) REFERENCES {TABLE_2} (id) ON DELETE CASCADE;
            CREATE INDEX {TABLE_MANY_2_MANY}_a ON "{TABLE_MANY_2_MANY}" ("{TABLE_1}_id");
            CREATE INDEX {TABLE_MANY_2_MANY}_b ON "{TABLE_MANY_2_MANY}" ("{TABLE_2}_id");
        """)

def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS model_a (
            id SERIAL PRIMARY KEY,
            name TEXT,
            create_uid INTEGER,
            create_date timestamp without time zone,
            write_uid INTEGER,
            write_date timestamp without time zone
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS model_b (
            id SERIAL PRIMARY KEY,
            name TEXT,
            create_uid INTEGER,
            create_date timestamp without time zone,
            write_uid INTEGER,
            write_date timestamp without time zone
        )
        """)

        rel = create_many_2_many_without_contraint(cur)
    conn.commit()
    return "model_a", "model_b", rel

def clean_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
        TRUNCATE TABLE model_a CASCADE;
        ALTER SEQUENCE model_a_id_seq RESTART;
        TRUNCATE TABLE model_b CASCADE;
        ALTER SEQUENCE model_b_id_seq RESTART;
        """)
        create_many_2_many_contraint(cur, drop=True)

def analyse_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
        ANALYZE model_a;
        ANALYZE model_b;
        ANALYZE model_a_model_b_rel;
        """)

def create_row_normal(conn, table, nb):
    with conn.cursor() as cur:
        cur.execute(f"""
        INSERT INTO {table} (name, create_uid, create_date, write_uid, write_date)
        SELECT
            'bla' || s::char,
            s % 10,
            now(),
            (s+1) % 10,
            now()
        FROM generate_series(1, {nb}) AS s
        """)
    conn.commit()

def create_many2many_row(conn, nb, concentration, size_t1, size_t2):
    split_val = 500_000
    done = 0
    while done < nb:
        s = time.time()
        todo = min((nb - done), split_val)
        done += todo
        with conn.cursor() as cur:
            if concentration is None:
                cur.execute(f"""
                INSERT INTO model_a_model_b_rel (model_a_id, model_b_id)
                SELECT ceil(random() * {size_t1 - 1}) + 1, ceil(random() * {size_t2 - 1}) + 1
                FROM generate_series(1, {todo}) as s
                ON CONFLICT DO NOTHING
                """)
            else:
                conc_normal_t1 = int(concentration * size_t1 / 100)
                conc_normal_t2 = int(concentration * size_t2 / 100)
                cur.execute(f"""
                INSERT INTO model_a_model_b_rel (model_a_id, model_b_id)
                SELECT t1, t2
                FROM UNNEST(
                    ARRAY(
                        SELECT array_agg(mod(abs(a)::integer, {size_t1 - 1}) + 1) FROM normal_rand({todo}, 0, {conc_normal_t1}) AS a
                    ), ARRAY(
                        SELECT array_agg(mod(abs(a)::integer, {size_t2 - 1}) + 1) FROM normal_rand({todo}, 0, {conc_normal_t2}) AS a
                    )) AS t(t1, t2)
                ON CONFLICT DO NOTHING
                """)
        conn.commit()
        print(f"{done}/{nb} ({time.time() - s} sec)")

    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM model_a_model_b_rel")
        res, = cur.fetchone()
    return res

def launch_test():

    def test_in_select_null(limit=None, order=None):
        return f"""
        SELECT id FROM model_a WHERE
        model_a.id IN (
            SELECT model_a_id FROM model_a_model_b_rel WHERE model_a_id IS NOT NULL
        )
        {'' if not order else 'ORDER BY ' + str(order)}
        {'' if not limit else 'LIMIT ' + str(limit)}"""

    def test_in_select(limit=None, order=None):
        return f"""
        SELECT id FROM model_a WHERE
        model_a.id IN (
            SELECT model_a_id FROM model_a_model_b_rel
        )
        {'' if not order else 'ORDER BY ' + str(order)}
        {'' if not limit else 'LIMIT ' + str(limit)}"""

    def test_exists(limit=None, order=None):
        return f"""
        SELECT id FROM model_a WHERE EXISTS (
            SELECT 1 FROM model_a_model_b_rel WHERE model_a_id = model_a.id
        )
        {'' if not order else 'ORDER BY ' + str(order)}
        {'' if not limit else 'LIMIT ' + str(limit)}"""

    def test_not_in_select_null(limit=None, order=None):
        return f"""
        SELECT id FROM model_a WHERE
        model_a.id NOT IN (
            SELECT model_a_id FROM model_a_model_b_rel WHERE model_a_id IS NOT NULL
        )
        {'' if not order else 'ORDER BY ' + str(order)}
        {'' if not limit else 'LIMIT ' + str(limit)}"""

    def test_not_in_select(limit=None, order=None):
        return f"""
        SELECT id FROM model_a WHERE
        model_a.id NOT IN (
            SELECT model_a_id FROM model_a_model_b_rel
        )
        {'' if not order else 'ORDER BY ' + str(order)}
        {'' if not limit else 'LIMIT ' + str(limit)}"""

    def test_not_exists(limit=None, order=None):
        return f"""
        SELECT id FROM model_a WHERE NOT EXISTS (
            SELECT 1 FROM model_a_model_b_rel WHERE model_a_id = model_a.id
        )
        {'' if not order else 'ORDER BY ' + str(order)}
        {'' if not limit else 'LIMIT ' + str(limit)}"""

    query_methods = [
        test_in_select_null,
        test_in_select,
        test_exists,
        test_not_in_select_null,
        test_not_in_select,
        test_not_exists
    ]
    limit_to_test = [
        1,
        80,
        1000,
        # None
    ]
    order_to_test = [
        "id DESC",
        "id",
        # None
    ]

    possibilities = list(itertools.product(limit_to_test, order_to_test, query_methods))

    res_time = defaultdict(list)
    res_explain = defaultdict(lambda: "TIMEOUT")
    res_res = {}

    print("- Get explain + result")
    pass_method = set()
    for limit, order, query_me in possibilities:
        key = (query_me.__name__, limit, order)
        try:
            with psycopg2.connect("dbname=master") as conn:
                with conn.cursor() as cur:
                    query = query_me(limit, order)

                    cur.execute("EXPLAIN " + query)
                    text = "\n".join(s for s, in cur.fetchall())
                    res_explain[key] = text

                    cur.execute(query)
                    res_res[key] = [str(s) for s, in cur.fetchall()]
                    # print(key)
                    # print(text)
        except psycopg2.errors.OperationalError as e:
            if "timeout" in str(e):
                pass_method.add(key)
            else:
                raise

    print(f"- Test time ({len(pass_method)} methods timeout)")
    for _ in range(10):
        for limit, order, query_me in random.sample(possibilities, len(possibilities)):
            key = (query_me.__name__, limit, order)
            if key in pass_method:
                continue
            try:
                with psycopg2.connect("dbname=master") as conn:
                    with conn.cursor() as cur:
                        query = query_me(limit, order)
                        s = time.time()
                        cur.execute(query)
                        end = time.time() - s
                        res_time[key].append(end)
            except psycopg2.errors.OperationalError as e:
                if "timeout" in str(e):
                    pass
                else:
                    raise

    # Check that result
    print("- Check res_res and explain:")
    for limit, order in itertools.product(limit_to_test, order_to_test):
        key0 = ("test_in_select_null", limit, order)
        key1 = ("test_in_select", limit, order)
        key2 = ("test_exists", limit, order)
        if key0 in res_res and key1 in res_res and key2 in res_res and order is not None:
            assert res_res[key0] == res_res[key1] == res_res[key2], f"Same result \n{res_res[key0]}\n{res_res[key1]}\n{res_res[key2]}"
        if res_explain[key2] != res_explain[key1]:
            print()
            print(key1, "vs", key2)
            print(res_explain[key1])
            print(res_explain[key2])

    # print("- Print RESULT:")
    # for limit, order, meth in possibilities:
    #     key = (meth.__name__, limit, order)
    #     values = res_time[key]
    #     if not values:
    #         print(key, "TIMEOUT 10 sec for each")
    #         continue
    #     print(key, f"took {fmean(values)} sec in average, the best: {min(values)} sec, the worst: {max(values)} sec ")

    print()
    return dict(res_time), dict(res_explain)


TestCase = NamedTuple('TestCase', [
    ('name', str),
    ('size_t1', int),
    ('size_t2', int),
    ('size_rel', int),
    ('concentration', float),  # 0 > c > inf, lower means firsts record will have more link that other
])

size_table_t1 = {
    # 'Very small': 100,
    'Small': 2_000,
    # 'Normal': 50_000,
    'Big': 1_000_000,
    # 'Very_big': 10_000_000,
}

size_table_t2 = {
    # 'Very small': 100,
    # 'Small': 2_000,
    'Normal': 50_000,
    # 'Big': 1_000_000,
    # 'Very_big': 10_000_000,
}

size_rel_factor = {
    'Almost not connected': 1 / 5,
    # 'Few connection': 1,
    'Connected': 5,
    # 'Highly connected': 20,
}

concentration = {
    'None': None,
    # 'Few': 50,
    'A Lot': 10,
    # 'Very highly Concentrate': 2,
}

TESTS: list[TestCase] = []
for st_str_t1, st_size_t1 in size_table_t1.items():
    for st_str_t2, st_size_t2 in size_table_t2.items():
        for srf_str, srf in size_rel_factor.items():
            for conc_str, conc in concentration.items():
                name = (f"T1: {st_str_t1}, T2: {st_str_t2}, Rel factor: {srf_str} with concentration {conc_str}")
                TESTS.append(TestCase(name, st_size_t1, st_size_t2, int(srf * (st_size_t1 + st_size_t2)), conc))

def launch_tests(file_to_save):
    # prepare_db
    with psycopg2.connect("dbname=master") as conn:
        activate_extention(conn)
        create_tables(conn)

    all_result = {}

    for test in TESTS:
        s = time.time()
        print("--------" * 5)
        print("Begin Test", test, "\n")
        with psycopg2.connect("dbname=master") as conn:
            clean_tables(conn)
            conn.commit()

            create_row_normal(conn, TABLE_1, test.size_t1)
            create_row_normal(conn, TABLE_2, test.size_t2)

            res = create_many2many_row(conn, test.size_rel, test.concentration, test.size_t1, test.size_t2)
            print(res, " rel has been created")

            with conn.cursor() as cur:
                create_many_2_many_contraint(cur)

            analyse_table(conn)
            conn.commit()

        all_result[test] = launch_test()

        print(f"One test finished in {time.time() - s} sec")

    with open(file_to_save, 'wb') as f:
        pickle.dump(all_result, f)

def interpreted_result(file):

    def get_fmean_3_best(values):
        if len(values) > 2:
            return fmean(sorted(values)[:3])
        else:
            return TIMEOUT_REQUEST

    by_methods = defaultdict(list)

    with open(file, 'rb') as f:
        all_result = pickle.load(f)
        for test in all_result:
            res_time, res_explain = all_result[test]
            limits = list(unique(key[1] for key in res_time))
            orders = list(unique(key[2] for key in res_time))
            for key, values in res_time.items():
                meth_name, limit, order = key
                by_methods[meth_name].extend(values)

            for limit, order in itertools.product(limits, orders):
                # Print when the exist is slower than the actual query
                # test_in_select_null < test_exists
                current_key = ('test_in_select_null', limit, order)
                exists_key = ('test_exists', limit, order)
                mean_current = get_fmean_3_best(res_time[current_key])
                mean_exists = get_fmean_3_best(res_time[exists_key])
                if mean_current < mean_exists:
                    print(f"For {test}, {current_key} < {exists_key} :\n{mean_current} < {mean_exists} sec")

                # test_not_in_select_null < test_not_exists
                not_current_key = ('test_not_in_select_null', limit, order)
                not_exists_key = ('test_not_exists', limit, order)
                not_mean_current = get_fmean_3_best(res_time[not_current_key])
                not_mean_exists = get_fmean_3_best(res_time[not_exists_key])
                if not_mean_current < not_mean_exists:
                    print(f"For {test}, {not_current_key} < {not_exists_key} :\n{not_mean_current} < {not_mean_exists} sec")

    for key, values in by_methods.items():
        print(key, fmean(values), " sec")

file = 'all_result.obj'

print(len(TESTS))
launch_tests(file)
# interpreted_result(file)
