# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PsMrpCostItem(models.Model):
    _name = 'ps.mrp.cost.item'

    # code = fields.Char(string='Number')
    name = fields.Char(string='Name')
    cost_type = fields.Selection(
        [('direct', 'DirectExpenses'), ('indirect', 'IndirectExpenses'), ('consumable', 'ConsumableMaterial')],
        string='Cost Type')
    product_ids = fields.Many2many('product.template', string='Product')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    @api.onchange('cost_type')
    def _onchange_expense_ids_product_ids(self):
        for rec in self:
            if rec.cost_type in ['indirect']:
                rec.product_ids = None
            elif rec.cost_type in ['direct', 'consumable']:
                pass

    @api.constrains('cost_type')
    def _check_ids(self):
        for rec in self:
            if rec.cost_type in ['indirect']:
                rec.product_ids = None
            elif rec.cost_type in ['direct', 'consumable']:
                pass