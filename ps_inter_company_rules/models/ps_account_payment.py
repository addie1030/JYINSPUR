# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    src_payment_id = fields.Many2one('account.payment', string='Source Payment ID')

    @api.multi
    def post(self):
        result = super(AccountPayment, self).post()
        if self.env.user.company_id.send_receipt_and_payment:
            for res in self:
                if self.src_payment_id:
                    return result
                partner_id = []
                for company_id in self.env['res.company'].sudo().search([]):
                    partner_id.append(company_id.partner_id.id)
                if res.partner_id.id not in partner_id:
                    return result
                company_id = res.partner_id.company_id.id
                journal_id = self.env['account.journal'].sudo().search(
                    [('company_id', '=', company_id), ('code', '=', res.journal_id.code)]).id
                if not journal_id:
                    raise ValidationError(_('No corresponding journal type has been set by the opposing unit.'))
                if not self.payment_use.contrast_payment_use:
                    raise ValidationError(_('收付款用途未设置对应的收付款用途，请维护对应的收付款用途'))
                vals = {
                    'payment_use': self.payment_use.contrast_payment_use.id,
                    'partner_id': self.env.user.company_id.partner_id.id,
                    'amount': res.amount,
                    'journal_id': journal_id,
                    'payment_date': res.payment_date,
                    'communication': res.communication,
                    'payment_transaction_id': res.payment_transaction_id,
                    'payment_method_id': 2,  # 付款方式为手动付款
                    'src_payment_id': res.id,
                }
                account_payment = self.env['account.payment'].sudo().create(vals)
                account_payment.sudo().update({
                    'company_id': company_id,
                })
        return result
