# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _

from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sdd_paying_mandate_id = fields.Many2one(comodel_name='sdd.mandate', help="Once this invoice has been paid with Direct Debit, contains the mandate that allowed the payment.", copy=False)


    def invoice_validate(self):
        """ Overridden to automatically trigger the payment of the invoice if a
        mandate is available.
        """
        res = super(AccountInvoice, self).invoice_validate()

        for record in self.filtered(lambda x: x.type in ['in_refund', 'out_invoice'] and x.residual != 0):
            usable_mandate = record._get_usable_mandate()
            if usable_mandate:
                record.sdd_paying_mandate_id = usable_mandate
                record.pay_with_mandate(usable_mandate)
        return res

    def pay_with_mandate(self, mandate):
        """ Uses the mandate passed in parameters to pay this invoice. This function
        updates the state of the mandate accordingly if it was of type 'one-off',
        changes the state of the invoice and generates the corresponding payment
        object, setting its state to 'posted'.
        """
        date_upper_bound = mandate.end_date or self.date_invoice
        if not(mandate.start_date <= self.date_invoice <= date_upper_bound):
            raise UserError(_("You cannot pay an invoice with a mandate that does not cover the moment when it was issued."))

        payment_method = self.env.ref('account_sepa_direct_debit.payment_method_sdd')
        payment_journal = mandate.payment_journal_id

        #This code is only executed if the mandate may be used (thanks to the previous UserError)
        payment = self.env['account.payment'].with_context(active_id=self.id, active_ids=self.ids).create({
                                                      'invoice_ids': [(4, self.id, None)],
                                                      'journal_id': payment_journal.id,
                                                      'payment_method_id': payment_method.id,
                                                      'amount': self.residual,
                                                      'currency_id': self.currency_id.id,
                                                      'payment_type': 'inbound',
                                                      'communication': self.reference or self.number,
                                                      'partner_type': 'customer',
                                                      'partner_id': mandate.partner_id.commercial_partner_id.id,
                                                      'payment_date': self.date_due or self.date_invoice})
        payment.post()
        return payment

    def _get_usable_mandate(self):
        """ returns the first mandate found that can be used to pay this invoice,
        or none if there is no such mandate.
        """
        return self.env['sdd.mandate']._get_usable_mandate(self.company_id.id, self.commercial_partner_id.id, self.date_invoice)

    def _track_subtype(self, init_values):
        """Overridden to log a different message when an invoice is paid using SDD.
        """
        self.ensure_one()
        if 'state' in init_values and self.state in ('in_payment', 'paid') and self.type == 'out_invoice' and self.sdd_paying_mandate_id:
            return 'account_sepa_direct_debit.sdd_mt_invoice_paid_with_mandate'
        return super(AccountInvoice, self)._track_subtype(init_values)
