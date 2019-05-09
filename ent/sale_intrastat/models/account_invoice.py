# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('partner_shipping_id')
    def _onchange_partner_shipping_id(self):
        res = super(AccountInvoice, self)._onchange_partner_shipping_id()
        self.intrastat_country_id = self.partner_shipping_id.country_id.intrastat and self.partner_shipping_id.country_id.id or False
        return res
