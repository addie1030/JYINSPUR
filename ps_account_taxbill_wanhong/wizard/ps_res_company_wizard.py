# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import UserError

class PsResCompany(models.TransientModel):
    _name = "ps.res.company"

    @api.multi
    def ps_tax_bill_register(self):
        return {'type': 'ir.actions.act_window_close'}