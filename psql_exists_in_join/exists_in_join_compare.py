from collections import defaultdict
from itertools import islice
import random

import psycopg2
import psycopg2.extensions
import psycopg2.errors

from utils.misc import psql_explain, psql_vacuum_analyse, psql_set_timeout

CONNECTION_PARAMS = "dbname=master"


tables = [
    'sale_order_tag_line_rel',
    'sale_order_tag',
    'sale_order_line',
    'sale_order',
]

rng = random.Random(1)

def drop_tables(cr):
    for t in tables:
        cr.execute(f"DROP TABLE IF EXISTS {t}")

def create_tables(cr):
    # I want 4 table:
    # - Sale Order (main table), have a one2many -> sale.order.line via 'sale_id'
    # - Sale Order Line (sub table) link to sale_id
    # - Sale Order Tag ()
    # - Many2many table between Sale Order Tab and Sale Order Line
    cr.execute("""
        CREATE TABLE sale_order (
            id SERIAL PRIMARY KEY,
            partner VARCHAR NOT NULL
            uniform_100 INT,
            float_uniform_100 FLOAT,
        )
    """)
    cr.execute("""
        CREATE TABLE sale_order_line (
            id SERIAL PRIMARY KEY,
            sale_id INT NOT NULL,
            uniform_100 INT,
            float_uniform_100 FLOAT,
            FOREIGN KEY (sale_id) REFERENCES sale_order (id)
        )
    """)
    cr.execute("""
        CREATE TABLE sale_order_tag (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            color INT
        )
    """)
    cr.execute("""
        CREATE TABLE sale_order_tag_line_rel (
            tag_id INT,
            line_id INT,
            PRIMARY KEY (tag_id, line_id),
            FOREIGN KEY (tag_id) REFERENCES sale_order_tag (id),
            FOREIGN KEY (line_id) REFERENCES sale_order_line (id)
        )
    """)

data_cases = {
    'small': {
        'nb_sale_order': 50_000,
        'nb_sale_order_line': 500_000,

        'sale_order_tags': ['urgent', 'safe', 'boring client', 'water', 'other'],
        'sale_order_tags_weight': [0.1, 0.1, 0.1, 0.1, 0.1],
        'nb_sale_order_tag_line_rel': 10000,
    },
}

def create_indexes(cr):
    cr.execute("""
    
    """)

def get_values_generator_so(**kwargs):
    states = list(kwargs['sale_order_state_proportion'].keys())
    states_w = list(kwargs['sale_order_state_proportion'].values())
    for i in range(kwargs['nb_sale_order']):
        yield (
            rng.choices(states, states_w, k=1)[0],
            f'partern_{i}',
        )

def get_values_generator_sol(**kwargs):
    for i in range(kwargs['nb_sale_order_line']):
        yield (
            rng.randint(1, kwargs['nb_sale_order']),
            rng.randint(0, 100),
            rng.random() * 100,
        )

def split_every(n, iterator, piece_maker=tuple):
    """Splits an iterable into length-n pieces. The last piece will be shorter
       if ``n`` does not evenly divide the iterable length.

       :param int n: maximum size of each generated chunk
       :param Iterable iterable: iterable to chunk into pieces
       :param piece_maker: callable taking an iterable and collecting each
                           chunk from its slice, *must consume the entire slice*.
    """
    piece = piece_maker(islice(iterator, n))
    while piece:
        yield piece
        piece = piece_maker(islice(iterator, n))

def fill_database(data_case):
    BATCH_SIZE_CREATION = 100_000

    with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cr:
        for i, pieces in enumerate(split_every(BATCH_SIZE_CREATION, get_values_generator_so(**data_case))):
            print(f"Insert {i * BATCH_SIZE_CREATION}/{data_case['nb_sale_order']} SO")
            cr.execute(f"""
                INSERT INTO sale_order (state, partner, uniform_100, float_uniform_100) VALUES {','.join(['%s'] * len(pieces))}
            """, pieces)

    with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cr:
        for pieces in split_every(BATCH_SIZE_CREATION, get_values_generator_sol(**data_case)):
            print(f"Insert {i * BATCH_SIZE_CREATION}/{data_case['nb_sale_order_line']} SOL ")
            cr.execute(f"""
                INSERT INTO sale_order_line (sale_id, qty, price) VALUES {','.join(['%s'] * len(pieces))}
            """, pieces)


SQL_alternative = {
    "sale.order.line - search - [order_id.state = 'draft']": {
        'in': """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
            WHERE (
                "sale_order_line"."sale_id" IN (
                    SELECT "sale_order"."id" FROM "sale_order" WHERE "sale_order"."state" = 'draft'
                )
            )
            ORDER BY "sale_order_line"."id"
        """,

        'exists':
        """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
            WHERE (
                EXISTS (
                    SELECT FROM "sale_order" WHERE "sale_order"."state" = 'draft' AND "sale_order"."id" = "sale_order_line"."sale_id"
                )
            )
            ORDER BY "sale_order_line"."id"
        """,

        'left join':
        """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
                LEFT JOIN "sale_order" ON "sale_order"."id" = "sale_order_line"."sale_id"
            WHERE "sale_order"."state" = 'draft'
            ORDER BY "sale_order_line"."id"
        """,

        'CTE, in':
        """
            WITH subquery AS (
                SELECT "sale_order"."id" FROM "sale_order" WHERE "sale_order"."state" = 'draft'
            )
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
            WHERE "sale_order_line"."sale_id" IN (SELECT "id" FROM "subquery")
            ORDER BY "sale_order_line"."id"
        """,

        # 'CTE, join':
        # """
        #     WITH subquery AS (
        #         SELECT * FROM "sale_order" WHERE "sale_order"."state" = 'draft'
        #     )
        #     SELECT "sale_order_line"."id"
        #     FROM "sale_order_line"
        #         LEFT JOIN "subquery" ON "subquery"."id" = "sale_order_line"."sale_id"
        #     WHERE "subquery"."id" IS NOT NULL
        #     ORDER BY "sale_order_line"."id"
        # """,
    },
    "sale.order.line - search - [order_id.state = 'draft' OR qty > 50000]": {
        'in': """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
            WHERE (
                "sale_order_line"."sale_id" IN (
                    SELECT "sale_order"."id" FROM "sale_order" WHERE "sale_order"."state" = 'draft'
                )
                OR "sale_order_line"."qty" > 50000
            )
            ORDER BY "sale_order_line"."id"
        """,

        'exists':
        """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
            WHERE (
                EXISTS (
                    SELECT FROM "sale_order" WHERE "sale_order"."state" = 'draft' AND "sale_order"."id" = "sale_order_line"."sale_id"
                )
                OR "sale_order_line"."qty" > 50000
            )
            ORDER BY "sale_order_line"."id"
        """,

        'left join':
        """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
                LEFT JOIN "sale_order" ON "sale_order"."id" = "sale_order_line"."sale_id"
            WHERE ("sale_order"."state" = 'draft') OR "sale_order_line"."qty" > 50000
            ORDER BY "sale_order_line"."id"
        """,

        'CTE, in':
        """
            WITH subquery AS (
                SELECT "sale_order"."id" FROM "sale_order" WHERE "sale_order"."state" = 'draft'
            )
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
            WHERE "sale_order_line"."sale_id" IN (SELECT "id" FROM "subquery") OR "sale_order_line"."qty" > 50000
            ORDER BY "sale_order_line"."id"
        """,
    },
    "sale.order.line - search - [order_id.state = 'draft' AND qty > 50000]": {
        'in': """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
            WHERE (
                "sale_order_line"."sale_id" IN (
                    SELECT "sale_order"."id" FROM "sale_order" WHERE "sale_order"."state" = 'draft'
                )
                AND "sale_order_line"."qty" > 50000
            )
            ORDER BY "sale_order_line"."id"
        """,

        'exists':
        """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
            WHERE (
                EXISTS (
                    SELECT FROM "sale_order" WHERE "sale_order"."state" = 'draft' AND "sale_order"."id" = "sale_order_line"."sale_id"
                )
                AND "sale_order_line"."qty" > 50000
            )
            ORDER BY "sale_order_line"."id"
        """,

        'left join':
        """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
                LEFT JOIN "sale_order" ON "sale_order"."id" = "sale_order_line"."sale_id"
            WHERE "sale_order"."state" = 'draft' AND "sale_order_line"."qty" > 50000
            ORDER BY "sale_order_line"."id"
        """,

        'CTE, in':
        """
            WITH subquery AS (
                SELECT "sale_order"."id" FROM "sale_order" WHERE "sale_order"."state" = 'draft'
            )
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
            WHERE "sale_order_line"."sale_id" IN (SELECT "id" FROM "subquery") AND "sale_order_line"."qty" > 50000
            ORDER BY "sale_order_line"."id"
        """,
    },
}

def one_data_case_test():
    result_explain = defaultdict(dict)
    for alternative, sql_requests in SQL_alternative.items():
        with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cr:
            res = None
            for case_str, sql_request in sql_requests.items():
                cr.execute(sql_request)
                current_res = tuple(cr.fetchall())
                if res and current_res != res:
                    print(f"{res} != {current_res}")
                    raise ValueError(f"ERROR: {case_str} doens't have the same result than the previous one for {alternative}")
                res = current_res

        with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cr:
            for case_str, sql_request in sql_requests.items():
                plan = psql_explain(cr, sql_request)
                result_explain[alternative][case_str] = plan

    for alternative, case_plans in result_explain.items():
        list_plan = list(case_plans.values())
        if len(set(list_plan)) != 1:
            print(f"\n=> Some queries has a different plan for {alternative} ({len(set(list_plan))}):")
            case_by_plan = defaultdict(list)
            for case, plan in case_plans.items():
                case_by_plan[plan].append(case)
            for plan, cases in case_by_plan.items():
                print("  ------------------------")
                print(f"These cases {cases} has this plan:\n{plan}")
                print("  ------------------------")
        else:
            print(f"\n=> {alternative} all plan is equals")


def main():
    psql_set_timeout(CONNECTION_PARAMS, 30)
    with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cur:
        cur.execute("SET jit_above_cost = 100000;")

    for str_case, data_case in data_cases.items():
        print(" ################# ", str_case, ' #####################')
        with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cr:
            drop_tables(cr)
            create_tables(cr)

        print('> Fill Database')
        fill_database(data_case)
        print('> Analyze Vaccum')
        psql_vacuum_analyse(CONNECTION_PARAMS, None)
        print('> Launch Test\n')
        one_data_case_test()

    with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cur:
        cur.execute("SET jit_above_cost = -1;")


# Issue with the EXISTS:

# the AlternativesSubPlan cost is "badly" compute
# And since In psql v14 this commit has been added:
# https://github.com/postgres/postgres/commit/41efb8340877e8ffd0023bb6b2ef22ffd1ca014d


# TODO Convert this stuff in a Odoo module to test it with expression.py 

if __name__ == '__main__':
    main()
