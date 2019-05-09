# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    subscription_count = fields.Integer(string='Subscriptions', compute='_subscription_count')

    def _subscription_count(self):
        subscription_data = self.env['sale.subscription'].read_group(domain=[('partner_id', 'in', self.ids)],
                                                                     fields=['partner_id'],
                                                                     groupby=['partner_id'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in subscription_data])
        for partner in self:
            partner.subscription_count = mapped_data.get(partner.id, 0)
