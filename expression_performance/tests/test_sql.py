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

    def test_populate(self):
        models = {
            'perf.tag': 0,
            'perf.parent': 1000,
            'perf.child': 500000,
        }
        for model, nb in models.items():
            self.env[model]._custom_populate(nb)
