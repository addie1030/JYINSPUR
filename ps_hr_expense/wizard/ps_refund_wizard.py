from odoo import models, fields, api, _


class PsReturnedMoney(models.TransientModel):
    _name = 'ps.returned.amount'

    amount_return_theoretical = fields.Float(string="Theoretical refund amount", readonly=True)
    amount_return_actual = fields.Float(string="Actual refund amount")

    @api.multi
    def confirm_refund(self):
        expense_request_id = self.env.context.get('expense_request_id')
        expense_request = self.env['ps.hr.expense.request'].browse(expense_request_id)
        partner_id = expense_request.employee_id.sudo().address_home_id.id
        journal_id = self.env['account.journal'].search([('type', '=', 'cash')], limit=1).id
        for rec in self:
            new_payment = self.env['account.payment'].create({
                'payment_use': self.env.ref('ps_account.payment_use_preset_expense_refund').id,
                'payment_type': 'inbound',
                'partner_type': 'supplier',
                'partner_id': partner_id,
                'amount': rec.amount_return_actual,
                'journal_id': journal_id,
                'payment_method_id': 1,
                'ps_expense_request_id': expense_request_id,
                'ps_is_repayment': True,
                'communication': '退费用申请借款',
            })
        expense_request.update({'payment_ids': new_payment})
