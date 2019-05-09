# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class PsStockInventoryAnalysisDispatch(models.Model):
    _name = 'ps.stock.price.dispatch'
    _description = 'Stock Price Dispatch'  # 库存价格分析
    _auto = False

    product_id = fields.Many2one('product.product', string='Product')  # 产品
    location_id = fields.Many2one('stock.location', string='Location')  # 库位
    product_uom = fields.Many2one('uom.uom', string='Uom')  # 单位
    qty_start = fields.Float(string='Qty Start', digits=dp.get_precision('ps_unit_price'))  # 期初数量
    qty_in = fields.Float(string='Qty In', digits=dp.get_precision('ps_unit_price'))  # 收入数量
    qty_out = fields.Float(string='Qty Out', digits=dp.get_precision('ps_unit_price'))  # 发出数量
    qty_balance = fields.Float(string='Qty Balance')  # 结存数量
