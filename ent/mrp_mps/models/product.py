# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # TODO pĥase 2: mps_warehouse_ids = fields.Many2many('stock.warehouse', 'MPS in Warehouses')
    mps_active = fields.Boolean('Active in MPS')
    mps_forecasted = fields.Float('Forecasted Target', default=0.0)
    mps_min_supply = fields.Float('Minimum to Supply', default=0.0)
    mps_max_supply = fields.Float('Maximum to Supply', default=0.0)
    mps_apply = fields.Datetime('Latest Apply')
    apply_active = fields.Boolean()

    @api.multi
    def do_forecast(self):
        # This is just the save button...
        self.ensure_one()
        if not self.mps_active:
            #... But it is good to delete the indirect when necessary
            self.env['sale.forecast.indirect'].search([('product_origin_id', '=', self.id)]).unlink()
            boms = self.env['mrp.bom.line'].search([('product_id','=',self.id)])
            boms.mapped('product_id').write({'apply_active': True})
        else:
            self.write({'apply_active': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
