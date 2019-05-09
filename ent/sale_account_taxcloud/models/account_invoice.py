# -*- coding: utf-8 -*-

from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _get_partner(self):
        return self.partner_shipping_id or super(AccountInvoice, self)._get_partner()
