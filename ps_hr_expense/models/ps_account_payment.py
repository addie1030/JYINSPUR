# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PsAccountPayment(models.Model):
    _inherit = 'account.payment'

    ps_expense_request_id = fields.Many2one('ps.hr.expense.request', string='Expense Request')
    ps_is_repayment = fields.Boolean(string='Refund', default=False)
    ps_is_loan = fields.Boolean(string='Loan', default=False)

    @api.model
    def create(self, vals):
        res = super(PsAccountPayment, self).create(vals)
        if self.env.context.get('expense_request_id', False):
            expense_request_id = self.env.context.get('expense_request_id')
            expense_request = self.env['ps.hr.expense.request'].search([('id', '=', expense_request_id)])
            for r in res:
                r.write({'ps_expense_request_id': expense_request_id,
                         'ps_is_repayment': True})
                expense_request.write({'payment_id': r.id})
        elif self.env.context.get('expense_request_payment', False):
            expense_request = self.env['ps.hr.expense.request'].browse(self.env.context.get('expense_request_payment'))
            for r in res:
                expense_request.write({'payment_id': r.id})
        return res

    @api.multi
    def post(self):
        res = super(PsAccountPayment, self).post()
        for r in self:
            if not r.ps_is_repayment and r.ps_expense_request_id.sheet_id.state == 'approve':
                r.ps_expense_request_id.compute_amount_theoretical()
            if r.ps_is_loan:
                r.ps_expense_request_id.amount_actual = r.amount
            if r.ps_is_repayment:
                amount_return_actual = r.ps_expense_request_id.amount_return_actual
                expense_request = r.ps_expense_request_id
                expense_request.write({'amount_return_actual': r.amount + amount_return_actual})
                if expense_request.amount_return_actual >= expense_request.amount_return_theoretical:
                    expense_request.write({'need_repayment': False})
        return res
