# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, _
from odoo.exceptions import UserError


class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.workorder'

    def action_print(self):
        if self.product_id.tracking == 'none':
            if self.product_id.uom_id.category_id.measure_type == 'unit':
                qty = int(self.qty_producing)
            else:
                qty = 1
            res = self.env.ref(
                'stock_zebra.label_barcode_product_product'
            ).report_action([self.product_id.id] * qty)
            if self.current_quality_check_id.point_id.device_id:
                res['device_id'] = self.current_quality_check_id.point_id.device_id.id
                res['id'] = self.env.ref('stock_zebra.label_barcode_product_product').id
            #button goes immediately to next step
            self._next()
            return res
        else:
            if self.final_lot_id:
                if self.product_id.uom_id.category_id.measure_type == 'unit':
                    qty = int(self.qty_producing)
                else:
                    qty = 1
                res =  self.env.ref(
                    'stock_zebra.label_lot_template'
                ).report_action([self.final_lot_id.id] * qty)
                if self.current_quality_check_id.point_id.device_id:
                    res['device_id'] = self.current_quality_check_id.point_id.device_id.id
                    res['id'] = self.env.ref('stock_zebra.label_lot_template').id
                # The button goes immediately to the next step
                self._next()
                return res
            else:
                raise UserError(_('You did not set a lot/serial number for '
                'the final product'))