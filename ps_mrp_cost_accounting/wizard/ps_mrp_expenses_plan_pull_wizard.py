# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class PsMrpExpensesPullWizard(models.Model):
    _name = 'ps.mrp.expenses.pull.wizard'
    _description = 'Ps Mrp Expenses Pull Wizard'

    period_id = fields.Many2one('ps.account.period', string='Account Period')  # 会计期间
    expenses_plan_ids = fields.One2many('ps.mrp.expenses.plan.pull', 'pull_wizard_id', string="Expenses Pull Plan",
                                        default=lambda self: self.env['ps.mrp.expenses.plan.pull'].search(
                                            []))  # 费用引入计划

    @api.multi
    def _get_values(self):
        """
        费用引入方案取数逻辑
        :return:
        """
        for rec in self:
            expenses_pull_lines = []
            date_start = rec.period_id.date_start
            date_end = rec.period_id.date_end
            account_moves = self.env['account.move'].search([('state', '=', 'posted')])
            move_ids = []
            for move in account_moves:
                move_ids.append(move.id)
            for expenses_plan in rec.expenses_plan_ids:
                if expenses_plan.is_pull:
                    for plan in expenses_plan.plan_ids:
                        expenses_pull_line = {}
                        expenses_id = plan.expenses_id  # 费用项目
                        expenses_src = plan.expenses_src  # 取数来源
                        account_id = plan.account_id  # 科目
                        account_direction = plan.account_direction  # 借贷方向
                        cost_account_id = plan.cost_account_id  # 成本中心
                        amount = 0
                        # 取数来源为'科目总账-总账凭证'
                        if expenses_src == 'account_voucher':
                            if account_direction == 'debit':
                                lines = self.env['account.move.line'].search(
                                    [('account_id', '=', account_id.id), ('debit', '!=', 0), ('move_id', 'in', move_ids),
                                     ('date', '>=', date_start),
                                     ('date', '<=', date_end)])
                                for line in lines:
                                    amount += line.debit
                            elif account_direction == 'credit':
                                lines = self.env['account.move.line'].search(
                                    [('account_id', '=', account_id.id), ('credit', '!=', 0),
                                     ('move_id', 'in', move_ids), ('date', '>=', date_start),
                                     ('date', '<=', date_end)])
                                for line in lines:
                                    amount += line.credit
                        expenses_pull_line.update({
                            'expenses_id': expenses_id.id,  # 费用项目
                            'expenses_src': expenses_src,  # 取数来源
                            'cost_account_id': cost_account_id.id,  # 成本中心
                            'amount': amount,  # 金额
                            'account_period_id': rec.period_id.id,  # 会计期间
                            'business_date': fields.Date.today(),  # 业务日期
                            'expenses_plan_id': plan.id,  # 费用引入方案id
                        })
                        expenses_pull_lines.append(expenses_pull_line)
        return expenses_pull_lines

    @api.multi
    def _set_values(self, expenses_pull_lines):
        """
        费用引入方案展示数据逻辑
        :param expenses_pull_lines:
        :return:
        """
        expenses_pull = self.env['ps.mrp.expenses.pull']
        for expenses_pull_line in expenses_pull_lines:
            expenses_pull_exit = expenses_pull.search(
                [('expenses_plan_id', '=', expenses_pull_line['expenses_plan_id']),
                 ('period_id', '=', expenses_pull_line['account_period_id'])])
            # 如果同一个期间的费用方案已经引入过，那么覆盖之前的，否则创建新的引入方案
            if expenses_pull_exit:
                expenses_pull_exit.update({
                    'expenses_id': expenses_pull_line['expenses_id'],
                    'date': expenses_pull_line['business_date'],
                    'cost_account_id': expenses_pull_line['cost_account_id'],
                    'amount': expenses_pull_line['amount'],
                    'expenses_src': expenses_pull_line['expenses_src'],
                })
            else:
                expenses_pull_exit.create({
                    'code': self.env['ir.sequence'].next_by_code('ps.mrp.expenses.plan.pull'),
                    'expenses_id': expenses_pull_line['expenses_id'],
                    'date': expenses_pull_line['business_date'],
                    'cost_account_id': expenses_pull_line['cost_account_id'],
                    'amount': expenses_pull_line['amount'],
                    'period_id': expenses_pull_line['account_period_id'],
                    'expenses_src': expenses_pull_line['expenses_src'],
                    'expenses_plan_id': expenses_pull_line['expenses_plan_id'],
                })
            # TODO 如果费用方案删除，但是之前已经被引入过，那么删除之前被引入的费用方案

    @api.multi
    def pull(self):
        expenses_pull_lines = self._get_values()
        self._set_values(expenses_pull_lines)
        self.unlink()