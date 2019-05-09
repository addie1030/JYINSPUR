# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Company(models.Model):
    _inherit = 'res.company'

    send_receipt_and_payment = fields.Boolean(string="Automatic Push of Receipt or Payment Documents")