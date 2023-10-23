import itertools
import string
from random import Random

from odoo import fields, models
from odoo.fields import Command
from odoo.tools import split_every


BATCH_SIZE_CREATION = 50_000

chars = string.ascii_letters + string.digits

def random_string(rng: Random, size=50):
    return ''.join(rng.choice(chars) for _ in range(size))


def random_distribution(rng: Random, type: str, len_ids: int):
    if type == 'uniform':
        return rng.randint(0, len_ids - 1)
    if type == 'gauss':
        standard_deviation = len_ids / 4
        # Approximately 95 % of values is on 50 % first ids
        res = int(abs(rng.gauss(0, standard_deviation)))
        if res > (len_ids - 1):  # retry
            return random_distribution(rng, 'gauss', len_ids)
        return res
    raise Exception(f"Unknow distribution {type!r}")


class BaseModelExtention(models.AbstractModel):
    _inherit = 'base'

    def _custom_populate(self, nb_to_create, **kwargs):
        rng = Random(f'{self._name} {nb_to_create}')
        generator = self._custom_populate_factories(rng, **kwargs)
        generator = itertools.islice(self._custom_populate_factories(rng), nb_to_create)
        generator = split_every(BATCH_SIZE_CREATION, generator)

        for i, pieces in enumerate(generator):
            print(f"Insert {self._name}: {i * BATCH_SIZE_CREATION}/{nb_to_create}")
            self.create(pieces)
            self.env.cr.commit()


class PerfTag(models.Model):
    _name = _description = 'perf.tag'
    _order = 'name'

    # TODO translate fields ?
    name = fields.Char('Name', required=True)
    color = fields.Integer('Color')
    line_ids = fields.Many2many('perf.line')

    def _custom_populate_factories(
            self,
            rng: Random,
        ):
        for _ in itertools.count():
            yield {
                'name': random_string(rng),
                'color': rng.randint(1, 11),
            }


class PerfContainer(models.Model):
    _name = _description = 'perf.container'

    name = fields.Char('Unique name')
    line_ids = fields.One2many('perf.line', 'container_id')
    state = fields.Selection(required=True, selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancel'),
        ('confirmed', 'Confirmed'),
        ('to_pay', 'To Pay'),
        ('paid', 'Paid'),
    ])
    main_tag_id = fields.Many2one('perf.tag')

    def _custom_populate_factories(
            self,
            rng: Random,
            main_tag_distribution=('uniform', 0.5),  # distribution, change to have
        ):
        ids_container = self.env['perf.tag'].search([])._ids
        selections = self._fields['state'].get_values(self.env)
        for i in itertools.count():
            main_tag_id = False
            if rng.random() > main_tag_distribution[1]:
                index = random_distribution(rng, main_tag_distribution[0], len(ids_container))
                main_tag_id = ids_container[index]
            yield {
                'name': f'SO{(10 - len(str(i))) * "0"}{i}',
                'main_tag_id': main_tag_id,
                'state': selections[random_distribution(rng, 'uniform', len(selections))],
            }


class PerfLine(models.Model):
    _name = _description = 'perf.line'
    _parent_store = True

    container_id = fields.Many2one('perf.container', 'Container', required=True)
    container_state = fields.Selection(related='container_id.state', store=True)
    qty = fields.Float()
    price = fields.Monetary('Price', 'currency_id')  # It is the slowest thing
    currency_id = fields.Many2one('res.currency', required=True)
    tag_ids = fields.Many2many('perf.tag')

    parent_id = fields.Many2one('perf.line')
    parent_path = fields.Char(index=True, unaccent=False)

    def _custom_populate_factories(
            self,
            rng: Random,
            container_distribution='uniform',
            currency_distribution='uniform',
            tags_distribution=(2, 'uniform'),
            parent_chance=0,
        ):
        container_ids = self.env['perf.container'].search([])._ids
        currency_ids = self.env['res.currency'].search([])._ids
        all_tag_ids = self.env['perf.tag'].search([])._ids

        for _ in itertools.count():

            index = random_distribution(rng, container_distribution, len(container_ids))
            container_id = container_ids[index]
            tag_ids = rng.choices(all_tag_ids, k=rng.randint(0, 3))

            yield {
                'container_id': container_id,
                'qty': rng.random() * 10000,
                'price': rng.random() * 10000,
                'currency_id': currency_ids[rng.randint(0, len(currency_ids) - 1)],
                'tag_ids': [Command.set(tag_ids)],
            }








