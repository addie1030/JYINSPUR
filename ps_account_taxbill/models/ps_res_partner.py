# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    ps_bank_name = fields.Many2one('res.bank', string='Banks')  # 开户行
    ps_bank_account = fields.Char(string='Bank Account') #开户银行账号

    @api.constrains('vat')
    def _check_customer_vat_length(self):
        for line in self:
            if line.vat and len(line.vat) not in [15, 18, 20]:
                raise ValidationError(_('Tax number must be 15, 18 or 20 digits in length.'))