# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    version = fields.Integer('Version', default=1)
    previous_routing_id = fields.Many2one('mrp.routing', 'Previous Routing')
    revision_ids = fields.Many2many('mrp.routing', compute='_compute_revision_ids')
    eco_ids = fields.One2many('mrp.eco', 'new_routing_id', 'ECOs')
    eco_count = fields.Integer('# ECOs', compute='_compute_eco_data')

    @api.one
    def _compute_revision_ids(self):
        previous_routings = self.env['mrp.routing']
        current = self
        while current.previous_routing_id:
            previous_routings |= current
            current = current.previous_routing_id
        self.revision_ids = previous_routings.ids

    @api.one
    def _compute_eco_data(self):
        self.eco_count = len(self.eco_ids)

    @api.multi
    def apply_new_version(self):
        """ Put old routing as deprecated - TODO Set to stage that is production_ready """
        self.write({'active': True})
        self.mapped('previous_routing_id').write({'active': False})
