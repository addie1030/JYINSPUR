# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import UserError

class PsApplyVatWizard(models.TransientModel):
    _name = "ps.apply.vat.wizard"
    _description = "VAT Application Notification"

    @api.multi
    def ps_apply_vat_confirm(self):
        return {'type': 'ir.actions.act_window_close'}

class PsDownloadVatWizard(models.TransientModel):
    _name = "ps.download.vat.wizard"
    _description = "VAT Downloading Notification"

    @api.multi
    def ps_download_vat_confirm(self):
        return {'type': 'ir.actions.act_window_close'}