from collections import defaultdict
import time
import pickle
from typing import NamedTuple
from statistics import NormalDist, fmean, pstdev
import random
import itertools

from misc import unique

import psycopg2
import psycopg2.extensions
import psycopg2.errors


COLOR = False

if COLOR:
    from misc import BOLD, GREEN, RED, RESET
else:
    BOLD, GREEN, RED, RESET = [""] * 4

PSQL_VERSION_BY_ODOO_V = {
    'v13': ['?'],
    'v14': ['?'],
    'v15': ['?'],
    'master': ['14'],
}

TIMEOUT_REQUEST = 5  # in sec
TABLE_1 = "model_a"
TABLE_2 = "model_b"
TABLE_MANY_2_MANY = f"{TABLE_1}_{TABLE_2}_rel"

ODOO_V13 = False  # use create_many_2_many_contraint_v_13 if True
CONNECTION_PARAMS = "dbname=master"
RESULT_FILE = 'results_odoo_v13.obj' if ODOO_V13 else 'results_odoo_master.obj'

def get_params_to_query(where, limit, order):
    return f"""
    {'' if not where else f'{where}'}
    {'' if not order else 'ORDER BY ' + str(order)}
    {'' if not limit else 'LIMIT ' + str(limit)}
    """

def test_in_select_null(where, limit, order):
    return """
    SELECT id FROM model_a WHERE
    model_a.id IN (
        SELECT model_a_id FROM model_a_model_b_rel WHERE model_a_id IS NOT NULL
    )
    """ + get_params_to_query(where, limit, order)

def test_in_select(where, limit, order):
    return """
    SELECT id FROM model_a WHERE
    model_a.id IN (
        SELECT model_a_id FROM model_a_model_b_rel
    )""" + get_params_to_query(where, limit, order)

def test_exists(where, limit, order):
    return """
    SELECT id FROM model_a WHERE EXISTS (
        SELECT 1 FROM model_a_model_b_rel WHERE model_a_id = model_a.id
    )""" + get_params_to_query(where, limit, order)

def test_not_in_select_null(where, limit, order):
    return """
    SELECT id FROM model_a WHERE
    model_a.id NOT IN (
        SELECT model_a_id FROM model_a_model_b_rel WHERE model_a_id IS NOT NULL
    )""" + get_params_to_query(where, limit, order)

def test_not_join_select_null(where, limit, order):
    return """
    SELECT id FROM model_a 
    LEFT JOIN model_a_model_b_rel ON (model_a_id = model_a.id)
    WHERE model_a_id IS NULL
    """ + get_params_to_query(where, limit, order)

def test_not_in_select(where, limit, order):
    return """
    SELECT id FROM model_a WHERE
    model_a.id NOT IN (
        SELECT model_a_id FROM model_a_model_b_rel
    )""" + get_params_to_query(where, limit, order)

def test_not_exists(where, limit, order):
    return """
    SELECT id FROM model_a WHERE NOT EXISTS (
        SELECT 1 FROM model_a_model_b_rel WHERE model_a_id = model_a.id
    )""" + get_params_to_query(where, limit, order)

def activate_extention(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
        CREATE EXTENSION IF NOT EXISTS "tablefunc";
        """)
    conn.commit()

def activate_timeout(conn, timeout):
    with conn.cursor() as cur:
        cur.execute(f"""
        ALTER ROLE odoo SET statement_timeout = '{timeout}s';
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
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_1} (
            id SERIAL PRIMARY KEY,
            name TEXT,
            create_uid INTEGER,
            create_date timestamp without time zone,
            write_uid INTEGER,
            write_date timestamp without time zone
        )
        """)

        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_2} (
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
        cur.execute(f"""
        TRUNCATE TABLE {TABLE_1} CASCADE;
        ALTER SEQUENCE {TABLE_1}_id_seq RESTART;
        TRUNCATE TABLE {TABLE_2} CASCADE;
        ALTER SEQUENCE {TABLE_2}_id_seq RESTART;
        TRUNCATE TABLE {TABLE_MANY_2_MANY} CASCADE;
        """)
        if ODOO_V13:
            create_many_2_many_contraint_v_13(cur, drop=True)
        else:
            create_many_2_many_contraint(cur, drop=True)

def analyse_table():
    with psycopg2.connect(CONNECTION_PARAMS) as conn:
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)  # Vaccum need to be done outside transaction block
        with conn.cursor() as cur:
            cur.execute("VACUUM ANALYZE model_a")
            cur.execute("VACUUM ANALYZE model_b")
            cur.execute("VACUUM ANALYZE model_a_model_b_rel")

def create_row_normal(conn, table, nb):
    split_val = 500_000
    done = 0
    while done < nb:
        s = time.time()
        todo = min((nb - done), split_val)
        done += todo
        with conn.cursor() as cur:
            cur.execute(f"""
            INSERT INTO {table} (name, create_uid, create_date, write_uid, write_date)
            SELECT
                'bla' || s::char,
                s % 10,
                now(),
                (s+1) % 10,
                now()
            FROM generate_series(1, {todo}) AS s
            """)
        conn.commit()
        print(f"create row of {table}, {done} / {nb} ({time.time() - s} sec)")

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
        print(f"rel creation: {done} / {nb} ({time.time() - s} sec)")

    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM model_a_model_b_rel")
        res, = cur.fetchone()
    return res

def launch_test():

    possibilities = list(itertools.product(limit_to_test, order_to_test, where_to_test, query_methods))

    res_time = defaultdict(list)
    res_explain = defaultdict(lambda: "TIMEOUT")
    res_res = {}

    print("- Get explain + result")
    pass_method = set()
    for limit, order, where, query_me in possibilities:
        key = (query_me.__name__, limit, order, where)
        try:
            with psycopg2.connect(CONNECTION_PARAMS) as conn:
                with conn.cursor() as cur:
                    query = query_me(where, limit, order)

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

    print(f"- Test time ({len(pass_method)} methods timeout : {pass_method})")
    for _ in range(10):
        for limit, order, where, query_me in random.sample(possibilities, len(possibilities)):
            key = (query_me.__name__, limit, order, where)
            if key in pass_method:
                continue
            try:
                with psycopg2.connect(CONNECTION_PARAMS) as conn:
                    with conn.cursor() as cur:
                        query = query_me(where, limit, order)
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
    print("- Check res_res:")
    for limit, order, where in itertools.product(limit_to_test, order_to_test, where_to_test):
        key1 = ("test_in_select_null", limit, order, where)
        key2 = ("test_exists", limit, order, where)
        if key1 in res_res and key2 in res_res and order is not None:
            assert res_res[key1] == res_res[key2], f"NOT the same result \n{res_res[key1]}\n{res_res[key2]}"
        key1 = ("test_not_in_select_null", limit, order, where)
        key2 = ("test_not_exists", limit, order, where)
        if key1 in res_res and key2 in res_res and order is not None:
            assert res_res[key1] == res_res[key2], f"NOT the same result \n{res_res[key1]}\n{res_res[key2]}"

    print()
    return dict(res_time), dict(res_explain)


TestCase = NamedTuple('TestCase', [
    ('name', str),
    ('size_t1', int),
    ('size_t2', int),
    ('size_rel', int),
    ('concentration', float),  # % of size of table -> stddev of the normal distribution
])
PerfCompare = NamedTuple('PerfCompare', [
    ('mean1', float),
    ('stddev1', float),
    ('mean2', float),
    ('stddev2', float),  # % of size of table -> stddev of the normal distribution
])
def perf_compare_str(perf: PerfCompare) -> str:
    return f"{perf.mean1:2.6f} +- {perf.stddev1:2.6f} < {perf.mean2:2.6f} +- {perf.stddev2:2.6f} sec(*{RED} {((perf.mean2 / perf.mean1 * 100)):7.3f} {RESET}%)"

# Test case attributes
size_table_1 = {
    # 'Very very small': 10,
    'Very small': 100,
    'Small': 2_000,
    'Normal': 50_000,
    # 'Big': 1_000_000,
    # 'Very_big': 10_000_000,
}
size_table_2 = {
    # 'Very very small': 10,
    'Very small': 100,
    'Small': 2_000,
    'Normal': 50_000,
    'Big': 1_000_000,
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
    'A Lot': 20,
    # 'Very highly Concentrate': 2,
}

TESTS: list[TestCase] = []
for st_str_t1, st_size_t1 in size_table_1.items():
    for st_str_t2, st_size_t2 in size_table_2.items():
        for srf_str, srf in size_rel_factor.items():
            for conc_str, conc in concentration.items():
                name = (f"T1: {st_str_t1}, T2: {st_str_t2}, Rel factor: {srf_str} with concentration {conc_str}")
                TESTS.append(TestCase(name, st_size_t1, st_size_t2, int(srf * (st_size_t1 + st_size_t2)), conc))

# Param by test (if you change it, the cache file should be deleted)
query_methods = [
    # test_in_select_null,
    # test_in_select,
    # test_exists,
    # test_not_in_select_null,
    test_not_join_select_null,
    # test_not_in_select,
    test_not_exists,
]
limit_to_test = [
    # 1,
    # 80,
    None
]
order_to_test = [
    # "id DESC",
    "id",
    # None
]
where_to_test = [
    None,
    # "create_uid < 5",  # half of data
    "AND create_uid < 2",  # 2/10 of data
    "OR create_uid < 2",  # 2/10 of data
]

def launch_tests(file_to_save):
    # prepare_db
    print(f"Launch {len(TESTS)} tests\n")
    with psycopg2.connect(CONNECTION_PARAMS) as conn:
        activate_extention(conn)
        create_tables(conn)

    all_ready = {}
    try:
        with open(file_to_save, 'rb') as f:
            all_ready = pickle.load(f)
            print(f"Read previous result in {RESULT_FILE}")
    except FileNotFoundError:
        pass

    tests = [t for t in TESTS if t not in all_ready]

    print(f"{str(len(TESTS) - len(tests))} tests skip (already done)")

    all_result = {}
    for i, test in enumerate(tests):
        start_time = time.time()
        print("--------" * 5)
        print("Begin Test", test, "\n")
        with psycopg2.connect(CONNECTION_PARAMS) as conn:
            activate_timeout(conn, TIMEOUT_REQUEST * 20)

        with psycopg2.connect(CONNECTION_PARAMS) as conn:
            clean_tables(conn)
            conn.commit()

            create_row_normal(conn, TABLE_1, test.size_t1)
            create_row_normal(conn, TABLE_2, test.size_t2)

            rel_size = create_many2many_row(conn, test.size_rel, test.concentration, test.size_t1, test.size_t2)
            print(rel_size, " rel has been created")

            with conn.cursor() as cur:
                if ODOO_V13:
                    create_many_2_many_contraint_v_13(cur)
                else:
                    create_many_2_many_contraint(cur)
            conn.commit()
        analyse_table()
        with psycopg2.connect(CONNECTION_PARAMS) as conn:
            activate_timeout(conn, TIMEOUT_REQUEST)

        res_time, res_explain = launch_test()
        all_result[test] = (res_time, res_explain, rel_size)
        print(f"-> Test ({i}/{len(tests)}) finished in {time.time() - start_time} sec")

    with open(file_to_save, 'wb') as f:
        print(f"Save result in {RESULT_FILE}")
        pickle.dump({**all_ready, **all_result}, f)

def interpreted_result(file):

    X_BEST = 5
    TIMEOUT_REQUEST_SIGMA = 0.000000000001  # NormalDist overlaps need a sigma

    def x_bests(values):
        return sorted(values)[:X_BEST]

    def means_std(values):
        values = x_bests(values)
        if len(values) > 1:
            return fmean(values), pstdev(values) * 2
        else:
            return TIMEOUT_REQUEST, TIMEOUT_REQUEST_SIGMA

    def statically_faster(values_1, values_2):
        """ Return true if values_1 is statically
        less (faster) than values_2
        """
        if len(values_1) > 1:
            values_1 = x_bests(values_1)
        else:
            values_1 = [TIMEOUT_REQUEST, TIMEOUT_REQUEST + TIMEOUT_REQUEST_SIGMA]
        if len(values_2) > 1:
            values_2 = x_bests(values_2)
        else:
            values_2 = [TIMEOUT_REQUEST, TIMEOUT_REQUEST + TIMEOUT_REQUEST_SIGMA]
        n1 = NormalDist.from_samples(values_1)
        n2 = NormalDist.from_samples(values_2)
        p = n1.overlap(n2)
        return p < 0.20 and fmean(values_1) < fmean(values_2)

    by_methods = defaultdict(list)
    faster_dict = defaultdict(list)
    faster_dict_method = defaultdict(list)
    each_timeout = []
    all_compare = 0

    with open(file, 'rb') as f:
        all_result = pickle.load(f)

        for test in all_result:
            # if test not in TESTS:
            #     pass
            res_time, res_explain, rel_size = all_result[test]

            def compare_two_test(key1, key2):
                if key1 not in res_time and key2 not in res_time:
                    each_timeout.append((test, key1, key2))
                if key1 not in res_time:
                    res_time[key1] = []
                if key2 not in res_time:
                    res_time[key2] = []

                if statically_faster(res_time[key1], res_time[key2]):
                    mean1, std1 = means_std(res_time[key1])
                    mean2, std2 = means_std(res_time[key2])
                    detail_perf = PerfCompare(mean1, std1, mean2, std2)
                    faster_dict[(key1, key2)].append((test, detail_perf))
                    if key1[0] != key2[0]:
                        faster_dict_method[(key1[0], key2[0])].append((test, key1, key2, detail_perf))
                elif statically_faster(res_time[key2], res_time[key1]):
                    mean1, std1 = means_std(res_time[key1])
                    mean2, std2 = means_std(res_time[key2])
                    detail_perf = PerfCompare(mean2, std2, mean1, std1)
                    faster_dict[(key2, key1)].append((test, detail_perf))
                    if key1[0] != key2[0]:
                        faster_dict_method[(key2[0], key1[0])].append((test, key2, key1, detail_perf))

            limits = list(unique(key[1] for key in res_time))
            orders = list(unique(key[2] for key in res_time))
            wheres = list(unique(key[3] for key in res_time))

            for key, values in res_time.items():
                meth_name, limit, order, where = key
                by_methods[meth_name].extend(values)

            for limit, order, where in itertools.product(limits, orders, wheres):
                # Print when the exist is slower than the actual query
                # test_in_select_null < test_exists
                all_compare += 1
                # current_key = ('test_in_select_null', limit, order, where)
                # exists_key = ('test_exists', limit, order, where)
                # compare_two_test(current_key, exists_key)

                # test_not_in_select_null < test_not_exists
                not_current_key = ('test_not_exists', limit, order, where)
                not_exists_key = ('test_not_join_select_null', limit, order, where)
                compare_two_test(not_current_key, not_exists_key)

                # print(test, not_exists_key, means_std(res_time[not_exists_key]))
                # print(res_explain[not_current_key])
                # print(res_explain[not_exists_key])

                if means_std(res_time[not_exists_key])[0] > 0.35:
                    print(test, not_exists_key, means_std(res_time[not_exists_key]))
                    print(res_explain[not_exists_key])

        # print(" ------------------------------------------------------ ")
        # for key, values in faster_dict.items():
        #     print(key[1:], len(values), ":")
        #     print("\n".join(str(v[0]) + " \n-> " + perf_compare_str(v[1]) for v in values))
        #     print()

        print("------------------------------------------------------ ")
        print("RESULT SUMMARIZE: \n")
        for methods, values in faster_dict_method.items():
            print("-------------------------- \n")
            timeout_faster = 0
            mean_gain = []
            for _, _, _, perf in values:
                mean1 = perf.mean1
                mean2 = perf.mean2
                if mean2 >= TIMEOUT_REQUEST:
                    timeout_faster += 1
                else:
                    mean_gain.append(mean2 / mean1 * 100)

            print(f"{BOLD}{methods[0]}{RESET} is faster than {BOLD}{methods[1]}{RESET} in {len(values)} cases (on {all_compare} cases)")
            if timeout_faster:
                print(f"Win because of {timeout_faster} timeout cases")
            if mean_gain:
                print(f"* {GREEN}{fmean(mean_gain):.2f}{RESET} % faster in average (for {len(mean_gain)} cases) (excluded timeout win)\n")

            combination = [(test, key1[1:], detail_perf) for test, key1, key2, detail_perf in values]
            combination = sorted(combination, key=lambda x: (x[2].mean2 < TIMEOUT_REQUEST, x[2].mean2 / x[2].mean1), reverse=True)

            def avg_str_mean(mean):
                return f"{(mean * 1000):4.2f}" if mean < TIMEOUT_REQUEST else "Timeout (> 5000)"

            def pourcentage(mean1, mean2):
                if mean2 >= TIMEOUT_REQUEST:
                    return ""
                return f" (* {GREEN}{(mean2 / mean1 * 100):6.2f}{RESET} %)"

            print("Faster + timeout win for these combination (sorted by the bigger gain):")
            print(f"· #table_1 <-> #table_rel (conc) <-> #table_2, {'(limit, order, where)':>35}: mean1 msec vs mean2 msec")
            print("\n".join(f"· {str(c[0].size_t1):>8} <-> {str(c[0].size_rel):>10} ({str(c[0].concentration):>4}) <-> {str(c[0].size_t2):>8}, {str(c[1]):>35}: {avg_str_mean(c[2].mean1):>7} msec vs {avg_str_mean(c[2].mean2):>7} msec{pourcentage(c[2].mean1, c[2].mean2)}" for c in combination))
            print()

            # Explain compare
            c_best = combination[0]
            print(f"Explain for the best win ({str(c_best[0].size_t1):>8} <-> {str(c_best[0].size_rel):>10} ({str(c_best[0].concentration):>4}) <-> {str(c_best[0].size_t2):>8}, {str(c_best[1]):>35}):")
            print(f"{BOLD}{methods[0]}{RESET} in {avg_str_mean(c_best[2].mean1):>7} msec:")
            res_explain = all_result[c_best[0]][1]
            print((methods[0],) + c_best[1])
            print(res_explain[(methods[0],) + c_best[1]])
            print()
            print(f"{BOLD}{methods[1]}{RESET} in : {avg_str_mean(c_best[2].mean2):>7} msec:")
            print(res_explain[(methods[1],) + c_best[1]])

        print("------------------------")
        print(f"There are {len(each_timeout)} cases where both methods has failed (test_in_select_null vs test_exists OR test_not_in_select_null vs test_not_exists)")

if __name__ == "__main__":
    # launch_tests(RESULT_FILE)
    interpreted_result(RESULT_FILE)
