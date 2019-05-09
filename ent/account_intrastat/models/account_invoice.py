# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    intrastat_transport_mode_id = fields.Many2one('account.intrastat.code', string='Intrastat Transport Mode',
        readonly=True, states={'draft': [('readonly', False)]}, domain="[('type', '=', 'transport')]")
    intrastat_country_id = fields.Many2one('res.country', string='Intrastat Country',
        help='Intrastat country, arrival for sales, dispatch for purchases',
        readonly=True, states={'draft': [('readonly', False)]}, domain=[('intrastat', '=', True)])

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id.country_id.intrastat:
            self.intrastat_country_id = self._get_intrastat_country_id()
        else:
            self.intrastat_country_id = False
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    intrastat_transaction_id = fields.Many2one('account.intrastat.code', string='Intrastat', domain="[('type', '=', 'transaction')]")
