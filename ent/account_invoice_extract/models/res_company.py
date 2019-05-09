# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    extract_show_ocr_option_selection = fields.Selection([
        ('no_send', 'Do not process bills'),
        ('manual_send', "Process bills on demand only"),
        ('auto_send', 'Process all bills automatically')], string="Send mode on invoices attachments",
        required=True, default='manual_send')