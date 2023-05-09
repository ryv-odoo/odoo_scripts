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
            print(f"Insert {self._name}: {i * BATCH_SIZE_CREATION}/{nb_to_create}")
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

class PerfContainer(models.Model):
    _name = _description = 'perf.container'
    _inherit = 'perf.abstract'
    _log_access = False

    line_ids = fields.One2many('perf.line', 'uniform_container_id')
    main_tag_id = fields.Many2one('perf.tag')



class PerfLine(models.Model):
    _name = _description = 'perf.line'
    _inherit = 'perf.abstract'
    _log_access = False
    _parent_store = True

    uniform_container_id = fields.Many2one('perf.container', 'Container', required=True)
    tag_ids = fields.Many2many('perf.tag')
    parent_id = fields.Many2one('perf.line')
    parent_path = fields.Char(index=True, unaccent=False)

    def _custom_populate_factories(self, rng: Random):
        ids_container = self.env['perf.container'].search([])._ids
        generator_ab = super()._custom_populate_factories(rng)
        for i in itertools.count():
            parent_id = False
            if i > 1 and rng.random() > 0.01:  # 25 % of set
                parent_id = rng.randint(1, i-1)
            yield next(generator_ab) | {
                'uniform_container_id': rng.choice(ids_container),
                'parent_id': parent_id,
            }


class PerfTag(models.Model):
    _name = _description = 'perf.tag'
    _inherit = 'perf.abstract'
    _log_access = False






