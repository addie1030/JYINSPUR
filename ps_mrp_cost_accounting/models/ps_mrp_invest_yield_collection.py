# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp


# 投入产量归集
class PsMrpInvestYieldCollection(models.Model):
    _name = "ps.mrp.invest.yield.collection"
    _description = 'Ps Mrp Invest Yield Collection'

    date = fields.Date(string='Business Date', default=fields.Date.context_today)  # 业务日期
    product_id = fields.Many2one('product.product', string='Product Name')  # 产品名称
    # TODO 暂时去掉生产类型，后期再添加
    mrp_production_id = fields.Many2one('mrp.production', string='Manufacturing Orders')  # 生产订单编号
    cost_account_id = fields.Many2one('ps.mrp.cost.accounting', string='Cost center')  # 成本中心
    product_qty = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string='Quantity To Product')  # 产品数量

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '投入产量归集'))
        return result