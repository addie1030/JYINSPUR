# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleContractTerm(models.Model):
    _name = 'ps.sale.contract.term'
    _description = 'sale contract term'

    sequence = fields.Integer(string='Sequence')
    content = fields.Html(string='Content')
    contract_id = fields.Many2one('ps.sale.contract', string='Contract', readonly=True)
    state = fields.Selection([('draft', "Draft"),
                              ('confirmed', "Confirmed"),
                              ('approved', "Approved"),
                              ('closed', "Closed"),
                              ('cancelled', "Cancelled")], string='Status', related='contract_id.state', default='draft',
                             readonly=True, index=True, track_visibility='onchange')


