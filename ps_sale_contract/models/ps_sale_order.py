# -*- coding: utf-8 -*-
import time

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_id = fields.Many2one('ps.sale.contract')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    contract_id = fields.Many2one('ps.sale.contract')
    contract_line_id = fields.Many2one('ps.sale.contract.line')



