import threading
import re
from itertools import combinations_with_replacement

import odoo
from odoo import api
from odoo.tests.common import BaseCase

def get_db_name():
    db = odoo.tools.config['db_name']
    # If the database name is not provided on the command-line,
    # use the one on the thread (which means if it is provided on
    # the command-line, this will break when installing another
    # database from XML-RPC).
    if not db and hasattr(threading.current_thread(), 'dbname'):
        return threading.current_thread().dbname
    return db


ratios_possible = [
    500, # 50 %
    50,  # 5 %
    5,   # 0.5 %
    0.5,  # 0.05 %
    0.01,  # 0.001 %
]


class TestPerformanceSQL(BaseCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.registry = odoo.registry(get_db_name())
        cls.addClassCleanup(cls.registry.reset_changes)
        cls.addClassCleanup(cls.registry.clear_caches)

        cls.cr = cls.registry.cursor()
        cls.addClassCleanup(cls.cr.close)

        cls.env = api.Environment(cls.cr, odoo.SUPERUSER_ID, {})

    def populate(self, nb_tag=0, nb_container=0, nb_line=0):
        models = {
            'perf.tag': nb_tag,
            'perf.container': nb_container,
            'perf.line': nb_line,
        }
        for model, nb in models.items():
            self.env[model]._custom_populate(nb)

        self.env.cr.execute('ANALYSE;')
        self.env.cr.commit()

    def create_indexes_many2one(self):
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS perf_line_uniform_container_id ON perf_line(uniform_container_id)")
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS perf_line_parent_id ON perf_line(parent_id)")
        self.env.cr.commit()

    def create_indexes_uniform(self):
        for table in ['perf_line', 'perf_container', 'perf_tag']:
            self.env.cr.execute(f"CREATE INDEX IF NOT EXISTS {table}_uniform_1000 ON {table}(uniform_1000)")
        self.env.cr.execute('ANALYSE;')
        self.env.cr.commit()

    def delete_indexes_uniform(self):
        for table in ['perf_line', 'perf_container', 'perf_tag']:
            self.env.cr.execute(f"DROP INDEX IF EXISTS {table}_uniform_1000")
        self.env.cr.execute('ANALYSE;')
        self.env.cr.commit()

    def delete_indexes_many2one(self):
        self.env.cr.execute("DROP INDEX IF EXISTS perf_line_uniform_container_id")
        self.env.cr.execute("DROP INDEX IF EXISTS perf_line_parent_id")
        self.env.cr.commit()

    def delete_all_indexes(self):
        self.delete_indexes_uniform()
        self.delete_indexes_many2one()

    def test_create_indexes_many2one(self):
        self.create_indexes_many2one()

    def test_create_indexes_uniform(self):
        self.create_indexes_uniform()

    def test_delete_all_indexes(self):
        self.delete_all_indexes()

    def test_truncate_everything(self):
        for table in ['perf_line', 'perf_container', 'perf_tag']:
            self.env.cr.execute(f'TRUNCATE "{table}" RESTART IDENTITY CASCADE')
        self.env.cr.commit()

    def test_one_sub_level_1_and(self):

        def domain_like(args):
            return [
                '&',
                ('uniform_1000', '<', args[0]),
                ('uniform_container_id.uniform_1000', '<', args[1]),
            ]

        queries = {
            'join': """
SELECT "perf_line"."id"
FROM "perf_line"
    JOIN "perf_container" ON "perf_line"."uniform_container_id" = "perf_container"."id"
WHERE
    "perf_line"."uniform_1000" < %s AND
    "perf_container"."uniform_1000" < %s
ORDER BY "perf_line"."id"
            """,

            'subselect': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."uniform_1000" < %s AND
    "perf_line"."uniform_container_id" IN (SELECT "perf_container"."id" FROM "perf_container" WHERE "perf_container"."uniform_1000" < %s)
ORDER BY "perf_line"."id"
            """,

            'exists': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."uniform_1000" < %s AND
    EXISTS (SELECT FROM "perf_container" WHERE "perf_container"."uniform_1000" < %s AND "perf_container"."id" = "perf_line"."uniform_container_id")
ORDER BY "perf_line"."id"
            """,
        }

        self.complete_test(
            'Level 1 - AND',
            queries,
            list(combinations_with_replacement(ratios_possible, 2)),
            domain_like,
        )

    def test_one_sub_level_1_or(self):

        def domain_like(args):
            return [
                '|',
                ('uniform_1000', '<', args[0]),
                ('uniform_container_id.uniform_1000', '<', args[1]),
            ]

        queries = {
            'join': """
SELECT "perf_line"."id"
FROM "perf_line"
    JOIN "perf_container" ON "perf_line"."uniform_container_id" = "perf_container"."id"
WHERE
    "perf_line"."uniform_1000" < %s OR
    "perf_container"."uniform_1000" < %s
ORDER BY "perf_line"."id"
            """,

            'subselect': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."uniform_1000" < %s OR
    "perf_line"."uniform_container_id" IN (SELECT "perf_container"."id" FROM "perf_container" WHERE "perf_container"."uniform_1000" < %s)
ORDER BY "perf_line"."id"
            """,

            'exists': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."uniform_1000" < %s OR
    EXISTS (SELECT FROM "perf_container" WHERE "perf_container"."uniform_1000" < %s AND "perf_container"."id" = "perf_line"."uniform_container_id")
ORDER BY "perf_line"."id"
            """,
        }

        self.complete_test(
            'Level 1 - OR',
            queries,
            list(combinations_with_replacement(ratios_possible, 2)),
            domain_like,
        )

    def test_two_sub_level_1_and(self):

        def domain_like(args):
            return [
                '&',
                ('parent_id.uniform_1000', '<', args[0]),
                ('uniform_container_id.uniform_1000', '<', args[1]),
            ]

        queries = {
            'join': """
SELECT "perf_line"."id"
FROM "perf_line"
    JOIN "perf_container" ON "perf_line"."uniform_container_id" = "perf_container"."id"
    LEFT JOIN "perf_line" AS "perf_line_1" ON "perf_line"."parent_id" = "perf_line_1"."id"
WHERE
    "perf_line_1"."uniform_1000" < %s AND
    "perf_container"."uniform_1000" < %s
ORDER BY "perf_line"."id"
            """,

            'subselect': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."parent_id" IN (SELECT "perf_line"."id" FROM "perf_line" WHERE "perf_line"."uniform_1000" < %s) AND
    "perf_line"."uniform_container_id" IN (SELECT "perf_container"."id" FROM "perf_container" WHERE "perf_container"."uniform_1000" < %s)
ORDER BY "perf_line"."id"
            """,

            'exists': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    EXISTS (SELECT FROM "perf_line" AS "perf_line_1" WHERE "perf_line_1"."uniform_1000" < %s AND "perf_line_1"."id" = "perf_line"."parent_id")
    AND EXISTS (SELECT FROM "perf_container" WHERE "perf_container"."uniform_1000" < %s AND "perf_container"."id" = "perf_line"."uniform_container_id")
ORDER BY "perf_line"."id"
            """,
        }

        self.complete_test(
            'Level 1 - 2 Subquery - And',
            queries,
            list(combinations_with_replacement(ratios_possible, 2)),
            domain_like,
        )

    def test_two_sub_level_1_or(self):

        def domain_like(args):
            return [
                '|',
                ('parent_id.uniform_1000', '<', args[0]),
                ('uniform_container_id.uniform_1000', '<', args[1]),
            ]

        queries = {
            'join': """
SELECT "perf_line"."id"
FROM "perf_line"
    JOIN "perf_container" ON "perf_line"."uniform_container_id" = "perf_container"."id"
    LEFT JOIN "perf_line" AS "perf_line_1" ON "perf_line"."parent_id" = "perf_line_1"."id"
WHERE
    "perf_line_1"."uniform_1000" < %s OR
    "perf_container"."uniform_1000" < %s
ORDER BY "perf_line"."id"
            """,

            'subselect': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."parent_id" IN (SELECT "perf_line"."id" FROM "perf_line" WHERE "perf_line"."uniform_1000" < %s) OR
    "perf_line"."uniform_container_id" IN (SELECT "perf_container"."id" FROM "perf_container" WHERE "perf_container"."uniform_1000" < %s)
ORDER BY "perf_line"."id"
            """,

            'exists': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    EXISTS (SELECT FROM "perf_line" AS "perf_line_1" WHERE "perf_line_1"."uniform_1000" < %s AND "perf_line_1"."id" = "perf_line"."parent_id")
    OR EXISTS (SELECT FROM "perf_container" WHERE "perf_container"."uniform_1000" < %s AND "perf_container"."id" = "perf_line"."uniform_container_id")
ORDER BY "perf_line"."id"
            """,
        }

        self.complete_test(
            'Level 1 - 2 Subquery - Or',
            queries,
            list(combinations_with_replacement(ratios_possible, 2)),
            domain_like,
        )

    def test_two_level_condition(self):
        def domain_like(args):
            return [
                ('parent_id.uniform_container_id.uniform_1000', '<', args[0])
            ]

        queries = {
            'join': """
SELECT "perf_line"."id"
FROM "perf_line"
    LEFT JOIN "perf_line" AS "perf_line_1" ON "perf_line_1"."id" = "perf_line"."parent_id"
    LEFT JOIN "perf_container" ON "perf_line_1"."uniform_container_id" = "perf_container"."id"
WHERE
    "perf_container"."uniform_1000" < %s
ORDER BY "perf_line"."id"
            """,

            'subselect': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."parent_id" IN (
        SELECT "perf_line"."id" FROM "perf_line"
        WHERE "perf_line"."uniform_container_id" IN (
            SELECT "perf_container"."id" FROM "perf_container"
            WHERE "perf_container"."uniform_1000" < %s
        )
    )
ORDER BY "perf_line"."id"
            """,

            'exists': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    EXISTS (
        SELECT FROM "perf_line" AS "perf_line_1"
        WHERE EXISTS (
            SELECT FROM "perf_container"
            WHERE "perf_container"."uniform_1000" < %s AND "perf_line_1"."uniform_container_id" = "perf_container"."id"
        ) AND "perf_line"."parent_id" = "perf_line_1"."id"
    )
ORDER BY "perf_line"."id"
            """,
        }

        self.complete_test(
            'Level 2 - For arguments',
            queries,
            list(combinations_with_replacement(ratios_possible, 1)),
            domain_like,
        )

    def complete_test(self, name_test, queries, args_combinaison, domain_like: callable):
        def launch_queries():
            result = {}
            for arguments in args_combinaison:
                res = None
                for name, query in queries.items():
                    self.env.cr.execute(query, arguments)
                    res_new = [id_ for id_, in self.env.cr.fetchall()]
                    if res and res != res_new:
                        raise Exception(f'{name} not the same result than the previous one: {name_test}')
                    res = res_new

                explain_dict = {}
                for name, query in queries.items():
                    self.env.cr.execute("EXPLAIN " + query, arguments)
                    explain_str = "\n".join(s for s, in self.env.cr.fetchall())
                    # Index Scan using perf_line_pkey on perf_line  (cost=17.16..6018.23 rows=75000 width=4)
                    start_cost, end_cost = re.search(r'cost=([\d\.]+)\.\.([\d\.]+) rows', explain_str).groups()
                    explain_dict[name] = (float(start_cost), float(end_cost), explain_str)

                result[arguments] = explain_dict

                if len(set(explain_dict.values())) == 1:
                    print(f"===> {name_test}: {domain_like(arguments)} : ALL the same, cost = {start_cost}")
                    continue

                print(f"===> {name_test}: {domain_like(arguments)}")
                for name, explain in explain_dict.items():
                    print(f'====> {name} : {explain[0]}..{explain[1]}')

            return result

        tables = ['nb_container', 'nb_line']
        sizes_table = [
            10_000,
            100_000,
            # 1_000_000,
            # 10_000_000
        ]

        size_table_combinations = combinations_with_replacement(sizes_table, len(tables))

        indexes_combinations = [
            [],
            # ['indexes_many2one'],
            # ['indexes_uniform'],
            ['indexes_many2one', 'indexes_uniform'],
        ]

        all_result = {}

        for sizes in size_table_combinations:

            args_creation = dict(zip(tables, sizes))

            print(f'=> For {args_creation} truncated and populate tables')
            self.test_truncate_everything()
            self.populate(**args_creation)

            for indexes in indexes_combinations:
                for index in indexes:
                    getattr(self, f'create_{index}')()

                print(f"==> Indexes : {indexes}")
                all_result[(
                    tuple(args_creation.items()),
                    tuple(indexes),
                )] = launch_queries()

                for index in indexes:
                    getattr(self, f'delete_{index}')()

