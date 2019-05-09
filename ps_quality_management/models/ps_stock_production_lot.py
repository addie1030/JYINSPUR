# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    ps_inventory_inspection_date = fields.Datetime(string='Inventory Inspection Date',
                                                   compute='_compute_inventory_inspection_date'
                                                   )

    @api.multi
    def _compute_inventory_inspection_date(self):
        '''复检日期 = (质检单完成的)入库日期 + 复检周期'''
        for record in self:
            move_ids = self.env['stock.move.line'].search(
                [('lot_id', '=', record.id), ('product_id', '=', record.product_id.id)])
            picking_ids = [move_id.picking_id for move_id in move_ids] if move_ids else None
            if picking_ids:
                check_date = []
                for picking_id in picking_ids:
                    if self.env['quality.point'].search([('product_tmpl_id', '=', record.product_id.product_tmpl_id.id), (
                            'picking_type_id', '=', picking_id.picking_type_id.id)]) and picking_id.date_done:
                        check_date.append(picking_id.date_done)
                    else:
                        continue
                quality_check_date_max = max(check_date) if check_date else None
                if quality_check_date_max:
                    inventory_inspection_time = self.env['product.template'].search(
                        [('id', '=', record.product_id.id)]).ps_inventory_inspection_time
                    if not inventory_inspection_time:
                        inventory_inspection_time = 0
                    record.ps_inventory_inspection_date = quality_check_date_max + relativedelta(
                        days=inventory_inspection_time)
