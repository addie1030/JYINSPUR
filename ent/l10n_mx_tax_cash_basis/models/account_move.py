# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def _get_amount_tax_cash_basis(self, amount, line):
        if (self.env.user.company_id.country_id != self.env.ref('base.mx') or
                not line.currency_id or not self.debit_move_id.currency_id or
                not self.credit_move_id.currency_id):
            return (super(AccountPartialReconcile, self)
                    ._get_amount_tax_cash_basis(amount, line))

        aml_obj = self.env['account.move.line']
        aml_ids = (self.debit_move_id | self.credit_move_id).ids
        # Use the payment date to compute currency conversion. When reconciling
        # an invoice and a credit note - we will use the greatest date of them.
        domain = [('id', 'in', aml_ids), ('invoice_id', '=', False)]
        move_date = aml_obj.search(domain, limit=1, order="date desc").date
        if not move_date:
            domain.pop()
            move_date = aml_obj.search(domain, limit=1, order="date desc").date
        return (
            line.amount_currency and line.balance and line.currency_id._convert(  # noqa
                line.amount_currency * amount / line.balance,
                line.company_id.currency_id, line.company_id, move_date) or 0.0)  # noqa
