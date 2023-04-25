import threading

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

    def test_a_populate(self):
        models = {
            'perf.tag': 0,
            'perf.parent': 100_000,
            'perf.child': 500_000,
        }
        for model, nb in models.items():
            self.env[model]._custom_populate(nb)

        self.env.cr.execute('ANALYSE;')

    def test_create_indexes_many2one(self):
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS perf_child_uniform_parent_id ON perf_child(uniform_parent_id)")
        self.env.cr.commit()

    def test_create_indexes_uniform(self):
        for table in ['perf_child', 'perf_parent', 'perf_tag']:
            self.env.cr.execute(f"CREATE INDEX IF NOT EXISTS {table}_float_uniform_1000 ON {table}(float_uniform_1000)")
        self.env.cr.commit()

    def test_delete_all_indexes(self):
        for table in ['perf_child', 'perf_parent', 'perf_tag']:
            self.env.cr.execute(f"DROP INDEX IF EXISTS {table}_float_uniform_1000")

        self.env.cr.execute("DROP INDEX IF EXISTS perf_child_uniform_parent_id")
        self.env.cr.commit()

    def test_join_or_left_join_required(self):
        simple = {
            'join': """
SELECT "perf_child"."id"
FROM "perf_child"
    JOIN "perf_parent" ON "perf_child"."uniform_parent_id" = "perf_parent"."id"
WHERE
    "perf_child"."float_uniform_1000" < %s
    AND "perf_parent"."float_uniform_1000" < %s
ORDER BY "perf_child"."id"
            """,
            'left join': """
SELECT "perf_child"."id"
FROM "perf_child"
    LEFT JOIN "perf_parent" ON "perf_child"."uniform_parent_id" = "perf_parent"."id"
WHERE
    "perf_child"."float_uniform_1000" < %s
    AND "perf_parent"."float_uniform_1000" < %s
ORDER BY "perf_child"."id"
            """,
        }
        ratio = [
            # child_selected_pourcent, parent_selected_pourcent
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


