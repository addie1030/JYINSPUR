# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ps_inventory_inspection_time = fields.Integer(string='Inventory Inspection Time')

    @api.onchange('tracking')
    def _onchange_ps_inventory_inspection_time(self):
        if self.tracking  == 'none':
            self.ps_inventory_inspection_time = 0
