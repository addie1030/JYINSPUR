# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Stored to allow being used in the financial reports as a groupby value (we need it since it's called via SQL)
    l10n_es_real_estate_id = fields.Many2one(string="Real Estate", related='invoice_id.l10n_es_real_estate_id', store=True, help="Real estate related to the invoice that created this move line, in case we are leasing it.", readonly=False)