# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResCurrency(models.Model):
    _inherit = "res.currency"

    ebay_available = fields.Boolean("Availability To Use For eBay API", readonly=True)
