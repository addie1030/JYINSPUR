# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools
from datetime import timedelta, datetime, time
from odoo.exceptions import UserError, ValidationError, Warning


class PsStockCostMaintenance(models.Model):
    _inherit = "stock.move"

    @api.onchange('price_unit')
    def set_item_value(self):
        if self.product_qty <= 0:
            return
        self.remaining_value = self.price_unit * self.remaining_qty
        self.value = self.price_unit * self.product_qty

    @api.onchange('value')
    def set_item_price_unit(self):
        if self.product_qty <= 0:
            return
        self.remaining_value = (self.value / self.product_qty) * self.remaining_qty
        self.price_unit = self.value / self.product_qty
