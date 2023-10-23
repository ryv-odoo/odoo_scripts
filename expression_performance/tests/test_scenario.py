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
        cls.addClassCleanup(cls.registry.clear_all_caches)

        cls.cr = cls.registry.cursor()
        cls.addClassCleanup(cls.cr.close)

        cls.env = api.Environment(cls.cr, odoo.SUPERUSER_ID, {})

    def compare_query(self, query1, query2):
        self.env.cr.execute("EXPLAIN " + query1)
        explain_1 = self.env.cr.fetchall()

        self.env.cr.execute("EXPLAIN " + query2)
        explain_2 = self.env.cr.fetchall()




        self.env.cr.execute(query1)
        self.env.cr.execute(query2)

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

    def test_db_scenario(self):
        self.populate(nb_tag=2, nb_container=500, nb_line=500_000)

        # Small without indexed
        # Small partially index
        # Small with index

    def test_related_store_vs_nostore_groupby(self):
        # self.populate(nb_tag=2, nb_container=50_000, nb_line=500_000)
        # container_state = fields.Selection(related='container_id.state', store=True)

        # Group by
        self.env.cr.execute("""
            SELECT COUNT(*), container_state
            FROM perf_line
            GROUP BY container_state
            ORDER BY container_state
            LIMIT 80
        """)

        self.env.cr.execute("""
            SELECT COUNT(*), container.state
            FROM perf_line
                LEFT JOIN perf_container as container ON container.id = perf_line.container_id
            GROUP BY container.state
            ORDER BY container.state
            LIMIT 80
        """)

        # Search
        self.env.cr.execute("""
            SELECT id
            FROM perf_line
            WHERE container_state = 'paid'
            ORDER BY id
            LIMIT 80
        """)

        self.env.cr.execute("""
            SELECT perf_line.id
            FROM perf_line
                LEFT JOIN perf_container as container ON container.id = perf_line.container_id
            WHERE container.state = 'paid'
            ORDER BY id
            LIMIT 80
        """)


    def test_truncate_all(self):
        self.env.cr.execute("TRUNCATE perf_line RESTART IDENTITY CASCADE")
        self.env.cr.execute("TRUNCATE perf_container RESTART IDENTITY CASCADE")
        self.env.cr.execute("TRUNCATE perf_tag RESTART IDENTITY CASCADE")
