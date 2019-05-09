# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    l10n_es_real_estate_id = fields.Many2one(string="Real Estate", comodel_name='l10n_es_reports.real.estate', help="Real estate related to this invoice, in case we are leasing it.")
    l10n_es_reports_mod347_invoice_type = fields.Selection(selection_add=[('real_estates', "Real estates operation")])

    @api.onchange('l10n_es_reports_mod347_invoice_type')
    def onchange_mod347_invoice_type(self):
        """ Onchange method making sure the l10n_es_real_estate_id field
        is reset to None in case the mod347 invoice type is changed from 'real
        estates' to something else """
        if self.l10n_es_reports_mod347_invoice_type != 'real_estates':
            self.l10n_es_real_estate_id = None

    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        rslt = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice, date, description, journal_id)
        rslt['l10n_es_real_estate_id'] = invoice.l10n_es_real_estate_id.id
        return rslt