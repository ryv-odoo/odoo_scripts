
import itertools
import time
import random
from collections import defaultdict
from datetime import datetime
from statistics import fmean, pstdev
from uuid import uuid4

import tabulate
from psycopg2.extensions import AsIs
from psycopg2.extras import execute_batch
import psycopg2

from misc import GREEN, RED, RESET, x_bests, frozendict

CONNECTION_PARAMS = "dbname=master"

TABLE = "model_a"


def create_table(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
            DROP TABLE IF EXISTS {TABLE};
            CREATE TABLE IF NOT EXISTS {TABLE} (
                id SERIAL PRIMARY KEY,
                name TEXT,
                some_int INTEGER,
                create_uid INTEGER,
                create_date timestamp without time zone,
                write_uid INTEGER,
                write_date timestamp without time zone
            );
            CREATE INDEX {TABLE}_gin ON {TABLE} USING gin(name gin_trgm_ops);
            """)
    conn.commit()

def create_row(conn, todo):
    with conn.cursor() as cur:
        cur.execute(f"""
        INSERT INTO {TABLE} (name, some_int, create_uid, create_date, write_uid, write_date)
        SELECT
            'bla,' || s::text,
            s % 10,
            s % 10,
            now(),
            (s+1) % 10,
            now()
        FROM generate_series(1, {todo}) AS s
        """)
    conn.commit()

# ---------------- Different implementation ------
# Current implentation
def update_key_values_current(cur, id_vals):
    # group record ids by vals, to update in batch when possible
    updates = defaultdict(list)
    for rid, vals in id_vals.items():
        updates[frozendict(vals)].append(rid)

    for vals, ids in updates.items():
        set_template = ', '.join(f'"{column_name}" = %s' for column_name in vals.keys())
        query = f'UPDATE "{TABLE}" SET {set_template} WHERE id IN %s'
        params = list(vals.values()) + [tuple(ids)]
        cur.execute(query, params)

def update_key_values_execute_batch(cur, id_vals):
    # group record ids by vals, to update in batch when possible
    updates = defaultdict(lambda: defaultdict(list))
    for rid, vals in id_vals.items():
        updates[tuple(vals)][tuple(vals.values())].append(rid)

    for keys, by_values in updates.items():
        set_template = ', '.join(f'"{column_name}" = %s' for column_name in keys)
        query = f'UPDATE "{TABLE}" SET {set_template} WHERE id IN %s'
        list_values = [list(values) + [tuple(ids)] for values, ids in by_values.items()]
        execute_batch(cur, query, list_values)

def update_key_without_bypass(cur, id_vals):
    updates = defaultdict(lambda: defaultdict(list))
    for rid, vals in id_vals.items():
        updates[tuple(vals)][tuple(vals.values())].append(rid)

    for keys, by_values in updates.items():
        sub_table = f"{TABLE}_tmp"
        column_temp = ', '.join(f'"{column_name}"' for column_name in ('ids',) + keys)
        set_template = ', '.join(f'"{column_name}" = "{sub_table}"."{column_name}"' for column_name in keys)
        values_template = ', '.join(['%s'] * len(by_values))
        query = f'UPDATE "{TABLE}" SET {set_template} FROM (VALUES {values_template}) AS {sub_table}({column_temp}) WHERE "{TABLE}"."id" = ANY("{sub_table}"."ids")'
        list_values = [tuple([ids] + list(values)) for values, ids in by_values.items()]
        cur.execute(query, list_values)

def update_key_with_bypass(cur, id_vals):
    updates = defaultdict(lambda: defaultdict(list))
    for rid, vals in id_vals.items():
        updates[tuple(vals)][tuple(vals.values())].append(rid)

    def batch_update(keys, by_values):
        sub_table = f"{TABLE}_tmp"
        column_temp = ', '.join(f'"{column_name}"' for column_name in ('ids',) + keys)
        set_template = ', '.join(f'"{column_name}" = "{sub_table}"."{column_name}"' for column_name in keys)
        values_template = ', '.join(['%s'] * len(by_values))
        query = f'UPDATE "{TABLE}" SET {set_template} FROM (VALUES {values_template}) AS {sub_table}({column_temp}) WHERE "{TABLE}"."id" = ANY("{sub_table}"."ids")'
        list_params = [tuple([ids] + list(values)) for values, ids in by_values.items()]
        cur.execute(query, list_params)

    def mono_update(keys, values, ids):
        set_template = ', '.join(f'"{column_name}" = %s' for column_name in keys)
        query = f'UPDATE "{TABLE}" SET {set_template} WHERE id IN %s'
        params = list(values) + [tuple(ids)]
        cur.execute(query, params)

    for keys, by_values in updates.items():
        if len(by_values) == 1:
            values, ids = next(iter(by_values.items()))
            mono_update(keys, values, ids)
        else:
            batch_update(keys, by_values)

# ---------------- Different data kind ------
# Worst case for new implem, best for current one
def data_key_uniform_values_uniform(ids):
    now = datetime.now()
    return {id_: {
        'some_int': 1,
        'create_uid': 6,
        'write_uid': 6,
        'create_date': now,
        'write_date': now,
    } for id_ in ids}


def data_key_uniform_values_change_2(ids):
    now = datetime.now()
    return {id_: {
        'some_int': i % 2,
        'create_uid': 6,
        'write_uid': 6,
        'create_date': now,
        'write_date': now,
    } for i, id_ in enumerate(ids)}

def data_key_uniform_values_change_40(ids):
    now = datetime.now()
    return {id_: {
        'some_int': i % 10,
        'create_uid': (i + 1) % 4,
        'write_uid': 6,
        'create_date': now,
        'write_date': now,
    } for i, id_ in enumerate(ids)}

def data_key_uniform_values_change_always(ids):
    now = datetime.now()
    return {id_: {
        'name': str(uuid4()),
        'some_int': id_,
        'create_uid': 6,
        'write_uid': 6,
        'create_date': now,
        'write_date': now,
    } for id_ in ids}

def data_key_change_3_values_uniform(ids):
    now = datetime.now()
    fields = ['some_int', 'create_uid', 'write_uid']
    res = {}
    for i, id_ in enumerate(ids):
        dict_values = {'create_date': now, 'write_date': now}
        dict_values[fields[i % len(fields)]] = 2
        res[id_] = dict_values
    return res

def data_key_change_3_values_change_4(ids):
    now = datetime.now()
    fields = ['some_int', 'create_uid', 'write_uid']
    res = {}
    for i, id_ in enumerate(ids):
        dict_values = {'create_date': now, 'write_date': now}
        dict_values[fields[i % len(fields)]] = i % 4
        res[id_] = dict_values
    return res


# NB_ROW = 1_000_000
NB_ROW = 200_000
NB_BATCH_UPDATE = 1_000
SPACE_BETWEEN_ID = 3

NB_TEST_BY_METHOD = 100
X_BESTS = 20

if __name__ == "__main__":
    print(f"Create table and row ({NB_ROW})")
    with psycopg2.connect(CONNECTION_PARAMS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            ALTER ROLE odoo SET statement_timeout = '60s';
            create extension IF NOT EXISTS pg_trgm;
            """)
        conn.commit()
    with psycopg2.connect(CONNECTION_PARAMS) as conn:
        create_table(conn)
        create_row(conn, NB_ROW)

    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    # from psycopg2.extras import LoggingConnection
    # logger = logging.getLogger("sql")

    with psycopg2.connect(CONNECTION_PARAMS) as conn:
    # with psycopg2.connect(CONNECTION_PARAMS, connection_factory=LoggingConnection) as conn:
        # conn.initialize(logger)
        update_methods = [
            update_key_values_current,
            update_key_values_execute_batch,
            update_key_without_bypass,
            update_key_with_bypass,
        ]
        data_methods = [
            data_key_uniform_values_uniform,
            data_key_uniform_values_change_2,
            data_key_uniform_values_change_40,
            data_key_uniform_values_change_always,
            data_key_change_3_values_uniform,
            data_key_change_3_values_change_4,
        ]
        test_cases = list(itertools.product(update_methods, data_methods))
        res = defaultdict(lambda: defaultdict(list))

        print("Warm up")
        for up_m, da_m in test_cases * 3:
            star_i = random.randint(1, NB_ROW - (NB_BATCH_UPDATE * SPACE_BETWEEN_ID))
            ids = list(range(star_i, (NB_BATCH_UPDATE * SPACE_BETWEEN_ID) + star_i, SPACE_BETWEEN_ID))
            id_vals = da_m(ids)
            with conn.cursor() as cur:
                up_m(cur, id_vals)
            conn.commit()

        print("launch test")
        shu_test = test_cases * NB_TEST_BY_METHOD
        random.shuffle(shu_test)
        for up_m, da_m in shu_test:
            star_i = random.randint(1, NB_ROW - (NB_BATCH_UPDATE * SPACE_BETWEEN_ID))
            ids = list(range(star_i, (NB_BATCH_UPDATE * SPACE_BETWEEN_ID) + star_i, SPACE_BETWEEN_ID))
            id_vals = da_m(ids)
            with conn.cursor() as cur:
                s = time.time()
                up_m(cur, id_vals)
            conn.commit()
            res[da_m.__name__][up_m.__name__].append((time.time() - s) * 1000)

    print(" Print result ")
    data_method_names = [da_m.__name__ for da_m in data_methods]
    update_method_names = [up_m.__name__ for up_m in update_methods]
    header = ["Data \\ method"] + update_method_names
    rows = []
    for i, da in enumerate(data_method_names):
        values_by_up = res[da]
        row = [da]
        best = min(fmean(x_bests(values, X_BESTS)) for values in values_by_up.values())
        worst = max(fmean(x_bests(values, X_BESTS)) for values in values_by_up.values())
        for up in update_method_names:
            values = values_by_up[up]
            str_row = f"{fmean(x_bests(values, X_BESTS)):>4.3f} +- {pstdev(x_bests(values, X_BESTS)):>4.3f} ms"
            if fmean(x_bests(values, X_BESTS)) == best:
                str_row = GREEN + str_row + RESET
            if fmean(x_bests(values, X_BESTS)) == worst:
                str_row = RED + str_row + RESET
            row.append(str_row)
        rows.append(row)
    print(tabulate.tabulate(rows, headers=header))
