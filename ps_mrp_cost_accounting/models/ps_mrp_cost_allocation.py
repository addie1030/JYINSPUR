# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PsMrpCostAllocation(models.Model):
    _name = 'ps.mrp.cost.allocation'

    period_id = fields.Many2one('ps.account.period', string='Account Period')  # 会计期间
    product_id = fields.Many2one('product.product', string='Product') # 产品名称
    cost_center = fields.Many2one('ps.mrp.cost.accounting', string='Cost Center') # 成本中心
    order_number = fields.Char(string='Order Number') # 工单编号
    plan_quantity = fields.Char(string='Plan Qty') # 计划数量
    initial_quantity = fields.Char(string='Initial Qty') # 期初数量
    initial_amount = fields.Char(string='Initial Amount') # 期初金额
    current_input_quantity = fields.Char(string='Current Input Qty') # 本期投入数量
    current_input_amount = fields.Char(string='Current Input Amount') # 本期投入金额
    accumulated_input_quantity = fields.Char(string='Accumulated Input Qty') # 累计投入数量
    accumulated_input_amount = fields.Char(string='Accumulated Input Amount') # 累计投入金额
    cumulative_quantity = fields.Char(string='Cumulative Qty') # 期末数量
    cumulative_amount = fields.Char(string='Cumulative Amount') # 期末金额
    complete_quantity_in = fields.Char(string='Complete Qty') # 本期完工数量
    complete_cost_in = fields.Char(string='Complete Cost') # 本期完工单位成本
    complete_amount_in = fields.Char(string='Complete Amount') # 本期完工金额
    complete_cumulative_quantity = fields.Char(string='Complete Cumulative Qty') # 累计完工数量
    complete_cumulative_cost = fields.Char(string='Complete Cumulative Cost') # 累计完工单位成本
    complete_cumulative_amount = fields.Char(string='Complete Cumulative Amount') # 累计完工金额


