import itertools
from random import Random

from odoo import fields, models
from odoo.tools import split_every


BATCH_SIZE_CREATION = 50_000

class BaseModelExtention(models.AbstractModel):
    _inherit = 'base'

    def _custom_populate(self, nb_to_create):
        rng = Random(f'{self._name} {nb_to_create}')
        generator = self._custom_populate_factories(rng)
        generator = itertools.islice(self._custom_populate_factories(rng), nb_to_create)
        generator = split_every(BATCH_SIZE_CREATION, generator)

        for i, pieces in enumerate(generator):
            print(f"Insert {i * BATCH_SIZE_CREATION}/{nb_to_create} {self._name}")
            self.create(pieces)
            self.env.cr.commit()

        return super()._populate_factories()

class PerfAbstract(models.AbstractModel):

    _name = _description = 'perf.abstract'

    unique_name = fields.Char('Unique name')
    uniform_1000 = fields.Integer('Uniform 1000')  # [0, 1000]
    float_uniform_1000 = fields.Float('Uniform 1000 Float')  # [0.0, 1000.0]

    def _create_indexes(self):
        pass

    def _custom_populate_factories(self, rng: Random):
        for i in itertools.count():
            yield {
                'unique_name': f'{self._name}/{i}',
                'uniform_1000': rng.randint(0, 1000),
                'float_uniform_1000': rng.random() * 1000,
            }

class PerfParent(models.Model):
    _name = _description = 'perf.parent'
    _inherit = 'perf.abstract'
    _log_access = False

    child_ids = fields.One2many('perf.child', 'uniform_parent_id')
    main_tag_id = fields.Many2one('perf.tag')



class PerfChild(models.Model):
    _name = _description = 'perf.child'
    _inherit = 'perf.abstract'
    _log_access = False

    uniform_parent_id = fields.Many2one('perf.parent', 'Parent', required=True)
    tag_ids = fields.Many2many('perf.tag')

    def _custom_populate_factories(self, rng: Random):
        ids_parent = self.env['perf.parent'].search([])._ids
        generator_ab = super()._custom_populate_factories(rng)
        for __ in itertools.count():
            yield next(generator_ab) | {
                'uniform_parent_id': rng.choice(ids_parent),
            }


class PerfTag(models.Model):
    _name = _description = 'perf.tag'
    _inherit = 'perf.abstract'
    _log_access = False






