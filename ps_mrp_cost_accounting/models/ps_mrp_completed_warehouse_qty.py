# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp


# 完工入库数量
class PsMrpCompletedWarehouseQty(models.Model):
    _name = "ps.mrp.completed.warehouse.qty"
    _description = 'Ps Mrp Completed Warehouse Quantity'

    stock_move_line_id = fields.Many2one('stock.move.line', string='Inventory Move')
    name = fields.Char(string='Document Orders')  # 单据编号
    date = fields.Date(string='Business Date', default=fields.Date.context_today)  # 业务日期
    product_id = fields.Many2one('product.product', string='Product Name')  # 产品名称
    cost_account_id = fields.Many2one('ps.mrp.cost.accounting', string='Cost center')  # 成本中心
    qty_done = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string='Quantity To Product')  # 产品数量
    # TODO 标准单位暂时不取
    stock_state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Stock Status',
        copy=False, readonly=True)
    stock_location_id = fields.Many2one('stock.location', string='Warehouse')  # 仓库
