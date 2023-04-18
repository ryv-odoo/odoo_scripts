from collections import defaultdict
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
            state VARCHAR NOT NULL,  -- Can be 'draft', 'to confirm', 'confirmed', 'cancel' or 'done'
            partner VARCHAR NOT NULL
        )
    """)
    cr.execute("""
        CREATE TABLE sale_order_line (
            id SERIAL PRIMARY KEY,
            sale_id INT NOT NULL,
            delivery_date DATE,
            qty FLOAT,
            amount FLOAT,
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
        'nb_sale_order': 50000,
        'sale_order_state_proportion': {
            'draft': 0.2,
            'to confirm': 0.2,
            'confirmed': 0.2,
            'cancel': 0.2,
            'done': 0.2,
        },

        'nb_sale_order_line': 500000,
        'qty_sale_order_line': [0, 100000],

        'sale_order_tags': ['urgent', 'safe', 'boring client', 'water', 'other'],
        'nb_sale_order_tag_line_rel': 10000,
    },
}

def create_indexes(cr):
    cr.execute("""
    
    """)

def fill_database(data_case):

    with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cr:
        states = []
        for state, proportion in data_case['sale_order_state_proportion'].items():
            states += [state] * int(proportion * data_case['nb_sale_order'])
        values_sale_order = tuple(
            (state, f'partern_{i}')
            for i, state in zip(range(data_case['nb_sale_order']), random.sample(states, k=len(states)))
        )

        cr.execute(f"""
            INSERT INTO sale_order (state, partner) VALUES {','.join(['%s'] * len(values_sale_order))}
        """, values_sale_order)

    with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cr:
        values_sale_order_line = tuple(
            (
                random.randint(1, data_case['nb_sale_order']),
                random.randint(data_case['qty_sale_order_line'][0], data_case['qty_sale_order_line'][1]),
            )
            for i in range(data_case['nb_sale_order_line'])
        )

        cr.execute(f"""
            INSERT INTO sale_order_line (sale_id, qty) VALUES {','.join(['%s'] * len(values_sale_order_line))}
        """, values_sale_order_line)


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

        'join':
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

        'join':
        """
            SELECT "sale_order_line"."id"
            FROM "sale_order_line"
                LEFT JOIN "sale_order" ON "sale_order"."id" = "sale_order_line"."sale_id"
            WHERE "sale_order"."state" = 'draft' OR "sale_order_line"."qty" > 50000
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

        # 'CTE, join':
        # """
        #     WITH subquery AS (
        #         SELECT * FROM "sale_order" WHERE "sale_order"."state" = 'draft'
        #     )
        #     SELECT "sale_order_line"."id"
        #     FROM "sale_order_line"
        #         LEFT JOIN "subquery" ON "subquery"."id" = "sale_order_line"."sale_id"
        #     WHERE "subquery"."id" IS NOT NULL OR "sale_order_line"."qty" > 50000
        #     ORDER BY "sale_order_line"."id"
        # """,
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

        'join':
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

        # 'CTE, join':
        # """
        #     WITH subquery AS (
        #         SELECT * FROM "sale_order" WHERE "sale_order"."state" = 'draft'
        #     )
        #     SELECT "sale_order_line"."id"
        #     FROM "sale_order_line"
        #         LEFT JOIN "subquery" ON "subquery"."id" = "sale_order_line"."sale_id"
        #     WHERE "subquery"."id" IS NOT NULL AND "sale_order_line"."qty" > 50000
        #     ORDER BY "sale_order_line"."id"
        # """,
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
                    raise ValueError(f"{case_str} doens't have the same result than the previous one for {alternative}")
                res = current_res

        for case_str, sql_request in sql_requests.items():
            with psycopg2.connect(CONNECTION_PARAMS) as conn, conn.cursor() as cr:
                plan = psql_explain(cr, sql_request)
                result_explain[alternative][case_str] = plan

    for alternative, case_plans in result_explain.items():
        list_plan = list(case_plans.values())
        if len(set(list_plan)) != 1:
            print(f"\n-> Some queries has a different plan for {alternative} ({len(set(list_plan))}):")
            case_by_plan = defaultdict(list)
            for case, plan in case_plans.items():
                case_by_plan[plan].append(case)
            for plan, cases in case_by_plan.items():
                print("  ------------------------")
                print(f"These cases {cases} has this plan:\n{plan}")
                print("  ------------------------")
        else:
            print(f"\n-> {alternative} all plan is equals")


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





if __name__ == '__main__':
    main()
