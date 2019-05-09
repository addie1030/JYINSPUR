# -*- coding: utf-8 -*-

from odoo import fields, models, _


class RemovalStrategy(models.Model):
    _inherit = 'product.removal'

    name = fields.Char('Name', required=True, translate=True)