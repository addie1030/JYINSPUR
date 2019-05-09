from odoo import api, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def process_reconciliation(self, counterpart_aml_dicts=None,
                               payment_aml_rec=None, new_aml_dicts=None):
        res = super(AccountBankStatementLine, self).process_reconciliation(
            counterpart_aml_dicts=counterpart_aml_dicts,
            payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
        payments = res.mapped('line_ids.payment_id')
        payments.write({
            'l10n_mx_edi_partner_bank_id': self.bank_account_id.id,
        })
        return res

    @api.onchange('partner_id')
    def _l10n_mx_onchange_partner_bank_id(self):
        self.bank_account_id = False
        if len(self.partner_id.bank_ids) == 1:
            self.bank_account_id = self.partner_id.bank_ids
