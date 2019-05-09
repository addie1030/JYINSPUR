# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    @api.multi
    def open_action(self):
        action = super(AccountJournal, self).open_action()
        view = self.env.ref('account.action_vendor_bill_template')
        if view and action["id"] == view.id:
            account_purchase_filter = self.env.ref('account_3way_match.account_invoice_filter_inherit_account_3way_match', False)
            action['search_view_id'] = account_purchase_filter and [account_purchase_filter.id, account_purchase_filter.name] or False
        return action

    def _get_open_bills_to_pay_query(self):
        """
        Overriden to take the 'release_to_pay' status into account when getting the
        vendor bills to pay (for other types of journal, its result
        remains unchanged).
        """
        if self.type == 'purchase':
            return ("""SELECT state, residual_signed as amount_total, currency_id AS currency
                   FROM account_invoice
                   WHERE journal_id = %(journal_id)s
                   AND (release_to_pay = 'yes' OR date_due < %(today)s)
                   AND state = 'open';""",
                   {'journal_id': self.id, 'today': fields.Date.today()})
        return super(AccountJournal, self)._get_open_bills_to_pay_query()
