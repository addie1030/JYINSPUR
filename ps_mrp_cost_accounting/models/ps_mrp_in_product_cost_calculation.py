# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp


# 在产品成本计算
class PsMrpInProductCostCalculation(models.Model):
    _name = "ps.mrp.in.product.cost.calculation"
    _description = 'Ps Mrp In Product Cost Calculation'

    period_id = fields.Many2one('ps.account.period', string='Account Period')  # 会计期间
    product_id = fields.Many2one('product.product', string='Product Name')  # 产品名称
    cost_account_id = fields.Many2one('ps.mrp.cost.accounting', string='Cost center')  # 成本中心
    name = fields.Char(string='Document Orders')  # 单据编号
    expenses_standard = fields.Many2one('ps.mrp.expenses.standard', string='Distribution Method')  # 分配方法
    initial_qty = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string='Initial Quantity')  # 期初数量
    initial_amount = fields.Float(digits=dp.get_precision('Product Price'), string='Initial Amount')  # 期初金额
    current_qty = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string='Current Quantity')  # 本期数量
    current_amount = fields.Float(digits=dp.get_precision('Product Price'), string='Current Amount')  # 本期金额
    end_qty = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string='End Quantity')  # 期末数量
    end_amount = fields.Float(digits=dp.get_precision('Product Price'), string='End Amount')  # 期末金额
    # date = fields.Date(string='Business Date', default=fields.Date.context_today)  # 业务日期
    state = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        copy=False)  # 单据状态
