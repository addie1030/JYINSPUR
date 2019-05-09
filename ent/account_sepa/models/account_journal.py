# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _default_outbound_payment_methods(self):
        vals = super(AccountJournal, self)._default_outbound_payment_methods()
        return vals + self.env.ref('account_sepa.account_payment_method_sepa_ct')

    @api.model
    def _enable_sepa_ct_on_bank_journals(self):
        """ Enables sepa credit transfer payment method on bank journals. Called upon module installation via data file.
        """
        sepa_ct = self.env.ref('account_sepa.account_payment_method_sepa_ct')
        euro = self.env.ref('base.EUR')
        if self.env.user.company_id.currency_id == euro:
            domain = ['&', ('type', '=', 'bank'), '|', ('currency_id', '=', euro.id), ('currency_id', '=', False)]
        else:
            domain = ['&', ('type', '=', 'bank'), ('currency_id', '=', euro.id)]
        for bank_journal in self.search(domain):
            bank_journal.write({'outbound_payment_method_ids': [(4, sepa_ct.id, None)]})
