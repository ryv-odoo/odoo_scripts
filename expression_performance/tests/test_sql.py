import threading
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

    def populate(self, nb_tag=0, nb_container=100_000, nb_line=500_000):
        models = {
            'perf.tag': nb_tag,
            'perf.container': nb_container,
            'perf.line': nb_line,
        }
        for model, nb in models.items():
            self.env[model]._custom_populate(nb)

        self.env.cr.execute('ANALYSE;')

    def create_indexes_many2one(self):
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS perf_line_uniform_container_id ON perf_line(uniform_container_id)")
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS perf_line_parent_id ON perf_line(parent_id)")
        self.env.cr.commit()

    def delete_all_indexes(self):
        for table in ['perf_line', 'perf_container', 'perf_tag']:
            self.env.cr.execute(f"DROP INDEX IF EXISTS {table}_float_uniform_1000")

        self.env.cr.execute("DROP INDEX IF EXISTS perf_line_uniform_container_id")
        self.env.cr.commit()

    def create_indexes_uniform(self):
        for table in ['perf_line', 'perf_container', 'perf_tag']:
            self.env.cr.execute(f"CREATE INDEX IF NOT EXISTS {table}_float_uniform_1000 ON {table}(float_uniform_1000)")
        self.env.cr.commit()

    def test_create_indexes_many2one(self):
        self.create_indexes_many2one()

    def test_create_indexes_uniform(self):
        self.create_indexes_uniform()

    def test_delete_all_indexes(self):
        self.delete_all_indexes()

    def test_one_level_condition(self):
        self.populate()
        self.env.cr.commit()

        ratios_possible = [
            500, # 50 %
            50,  # 5 %
            5,   # 0.5 %
            0.5,  # 0.05 %
            0.01,  # 0.001 %
        ]

        # For [<condition_1> line AND <condition_2> line.parent_id] on line
        queries = {
            'join': """
SELECT "perf_line"."id"
FROM "perf_line"
    JOIN "perf_container" ON "perf_line"."uniform_container_id" = "perf_container"."id"
WHERE
    "perf_line"."float_uniform_1000" < %s AND
    "perf_container"."float_uniform_1000" < %s
ORDER BY "perf_line"."id"
            """,
            'subselect': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."float_uniform_1000" < %s AND
    "perf_line"."uniform_container_id" IN (SELECT "perf_container"."id" FROM "perf_container" WHERE "perf_container"."float_uniform_1000" < %s)
ORDER BY "perf_line"."id"
            """,
            'exists': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."float_uniform_1000" < %s AND
    EXISTS (SELECT FROM "perf_container" WHERE "perf_container"."float_uniform_1000" < %s AND "perf_container"."id" = "perf_line"."uniform_container_id")
ORDER BY "perf_line"."id"
            """,
        }

        for line_ratio, container_ratio in combinations_with_replacement(ratios_possible, 2):
            arguments = [line_ratio, container_ratio]
            res = None
            for name, query in queries.items():
                self.env.cr.execute(query, arguments)
                res_new = [id_ for id_, in self.env.cr.fetchall()]
                if res and res != res_new:
                    raise Exception(f'{name} not the same result than the previous one')

            explain_dict = {}
            for name, query in queries.items():
                self.env.cr.execute("EXPLAIN " + query, arguments)
                explain_dict[name] = "\n".join(s for s, in self.env.cr.fetchall())

            if len(set(explain_dict.values())) == 1:
                print("AND - For arguments - All the same", arguments)
                continue
            
            print()
            print('AND - For arguments', arguments)
            for name, explain in explain_dict.items():
                print(f'=> {name} : ')
                print(explain)

        # For [<condition_1> line OR <condition_2> line.parent_id] on line
        queries = {
            'join': """
SELECT "perf_line"."id"
FROM "perf_line"
    JOIN "perf_container" ON "perf_line"."uniform_container_id" = "perf_container"."id"
WHERE
    "perf_line"."float_uniform_1000" < %s OR
    "perf_container"."float_uniform_1000" < %s
ORDER BY "perf_line"."id"
            """,
            'subselect': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."float_uniform_1000" < %s OR
    "perf_line"."uniform_container_id" IN (SELECT "perf_container"."id" FROM "perf_container" WHERE "perf_container"."float_uniform_1000" < %s)
ORDER BY "perf_line"."id"
            """,
            'exists': """
SELECT "perf_line"."id"
FROM "perf_line"
WHERE
    "perf_line"."float_uniform_1000" < %s OR
    EXISTS (SELECT FROM "perf_container" WHERE "perf_container"."float_uniform_1000" < %s AND "perf_container"."id" = "perf_line"."uniform_container_id")
ORDER BY "perf_line"."id"
            """,
        }

        for line_ratio, container_ratio in combinations_with_replacement(ratios_possible, 2):
            arguments = [line_ratio, container_ratio]
            res = None
            for name, query in queries.items():
                self.env.cr.execute(query, arguments)
                res_new = [id_ for id_, in self.env.cr.fetchall()]
                if res and res != res_new:
                    raise Exception(f'{name} not the same result than the previous one')

            explain_dict = {}
            for name, query in queries.items():
                self.env.cr.execute("EXPLAIN " + query, arguments)
                explain_dict[name] = "\n".join(s for s, in self.env.cr.fetchall())

            if set(explain_dict.values()) == 1:
                continue

            print()
            print('OR - For arguments', arguments)
            for name, explain in explain_dict.items():
                print(f'=> {name} : ')
                print(explain)

    def test_join_or_left_join_required(self):
        simple = {
            'join': """
SELECT "perf_line"."id"
FROM "perf_line"
    JOIN "perf_container" ON "perf_line"."uniform_container_id" = "perf_container"."id"
WHERE
    "perf_line"."float_uniform_1000" < %s
    AND "perf_container"."float_uniform_1000" < %s
ORDER BY "perf_line"."id"
            """,
            'left join': """
SELECT "perf_line"."id"
FROM "perf_line"
    LEFT JOIN "perf_container" ON "perf_line"."uniform_container_id" = "perf_container"."id"
WHERE
    "perf_line"."float_uniform_1000" < %s
    AND "perf_container"."float_uniform_1000" < %s
ORDER BY "perf_line"."id"
            """,
        }
        ratio = [
            # line_selected_pourcent, parent_selected_pourcent
            (500, 500),   # 50 %
            (50, 50),   # 5 %
            (50, 10),
            (0.5, 10),
            (50, 0.5),
            (0.5, 0.5),
            (0.1, 0.1),  # 0.01 %
        ]

        for r in ratio:
            self.env.cr.execute(simple['join'], r)
            res_join = [id_ for id_, in self.env.cr.fetchall()]

            self.env.cr.execute(simple['left join'], r)
            res_left_join = [id_ for id_, in self.env.cr.fetchall()]

            if res_join != res_left_join:
                print(res_join)
                print(res_left_join)
                raise Exception("Not the same result")

            self.env.cr.execute("EXPLAIN " + simple['join'], r)
            res_join = "\n".join(s for s, in self.env.cr.fetchall())

            self.env.cr.execute("EXPLAIN " + simple['left join'], r)
            res_left_join = "\n".join(s for s, in self.env.cr.fetchall())

            if res_join != res_left_join:
                print("FOR : ", r)
                print(res_join)
                print("<>")
                print(res_left_join)
                print()


