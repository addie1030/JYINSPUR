# -*- coding: utf-8 -*-
from odoo import fields, models, api


class CoreValue(models.Model):
    _name = 'ps.core.value'
    _description = 'The cash flow statement '

    name = fields.Char(string='The name of the ')
    type = fields.Char(string='type ', default='cash_id')
    note = fields.Text(string='instructions ')
    active = fields.Boolean(string='To enable the ', default=True)
    core_value_type = fields.Selection(string='Cash flow type ',
                                       selection=[('receive', 'received '), ('pay', 'spending '), ('cash_transfer', 'Cash transfers ')],
                                       default='receive')
    company_id = fields.Many2one('res.company', 'The company ', default=lambda self: self.env.user.company_id,
                                 ondelete='cascade')
