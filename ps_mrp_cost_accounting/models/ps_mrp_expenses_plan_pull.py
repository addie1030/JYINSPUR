# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


# 费用引入方案
class PsMrpExpensesPlanPull(models.Model):
    _name = 'ps.mrp.expenses.plan.pull'
    _description = 'Ps Mrp Expenses Plan Pull'

    is_pull = fields.Boolean(string='Is pull', default=False)  # 是否勾选费用引入方案
    code = fields.Char(string='Number')  # 方案编号
    name = fields.Char(string='Name')  # 方案名称
    plan_ids = fields.One2many('ps.mrp.expenses.plan', 'plan_pull_id', string='Store Formula')
    company_id = fields.Many2one('res.company', string='Company')
    pull_wizard_id = fields.Many2one('ps.mrp.expenses.pull.wizard')  # 关联Pull Wizard


# 费用取数条件
class PsMrpExpensesPlan(models.Model):
    _name = 'ps.mrp.expenses.plan'
    _description = 'Ps Mrp Expenses Plan'

    expenses_id = fields.Many2one('ps.mrp.expense.item', string='Expense Item')  # 费用项目
    expenses_src = fields.Selection([('account_voucher', 'Account_Voucher')], string='Source of number')  # 取数来源
    account_id = fields.Many2one('account.account', string='Account')  # 科目
    account_direction = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], string='Account Direction')  # 科目方向
    company_id = fields.Many2one('res.company', string='Company')  # 公司
    cost_account_id = fields.Many2one('ps.mrp.cost.accounting', string='Cost center')  # 成本中心
    plan_pull_id = fields.Many2one('ps.mrp.expenses.plan.pull', string='Expenses Plan Pull')  # 关联

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '费用引入方案'))
        return result


# 费用引入展示数据
class PsMrpExpensesPull(models.Model):
    _name = 'ps.mrp.expenses.pull'
    _description = 'Ps Mrp Expenses Pull'

    code = fields.Char(string='Number')  # 单据编号
    expenses_id = fields.Many2one('ps.mrp.expense.item', string='Expense Item')  # 费用项目
    date = fields.Date(string='Business Date', default=fields.Date.context_today)  # 业务日期
    cost_account_id = fields.Many2one('ps.mrp.cost.accounting', string='Cost center')  # 成本中心
    amount = fields.Float('Amount')  # 金额
    period_id = fields.Many2one('ps.account.period', string='Account Period')  # 会计期间
    expenses_src = fields.Selection([('account_voucher', 'Account_Voucher')], string='Source Of Number')  # 取数来源
    expenses_plan_id = fields.Many2one('ps.mrp.expenses.plan', string='Expenses Plan')  # 费用引入方案

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '费用引入'))
        return result
