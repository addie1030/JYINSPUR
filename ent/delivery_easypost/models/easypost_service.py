# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class EasypostService(models.Model):
    _name = 'easypost.service'
    _description = 'Easypost Service'

    name = fields.Char('Service Level Name', index=True)
    easypost_carrier = fields.Char('Carrier Prefix', index=True)
