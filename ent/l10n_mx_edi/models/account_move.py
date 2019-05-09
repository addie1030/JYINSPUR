# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        """Create payment complement with a full reconciliation"""
        res = super(AccountMoveLine, self).reconcile(
            writeoff_acc_id, writeoff_journal_id)
        # return if the call is not from a manual reconciliation
        if not self._context.get('l10n_mx_edi_manual_reconciliation', True):
            return res
        for pay in self.mapped('payment_id'):
            pay.write({'invoice_ids': [
                (6, 0, pay.reconciled_invoice_ids.ids)]})
            if pay.l10n_mx_edi_is_required() and pay.l10n_mx_edi_pac_status != 'signed':
                pay.l10n_mx_edi_cfdi_name = ('%s-%s-MX-Payment-10.xml' % (
                    pay.journal_id.code, pay.name))
                pay._l10n_mx_edi_retry()
        return res
