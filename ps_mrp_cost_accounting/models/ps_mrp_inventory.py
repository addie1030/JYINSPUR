# -*- coding: utf-8 -*-

import time
import math

from datetime import date, datetime
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools
from odoo.addons import decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero

class PsMrpInventory(models.Model):
    _name = 'ps.mrp.inventory'


    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])],
        readonly=True, required=True,
        states={'confirmed': [('readonly', False)]})
    mrp_cost_accounting_id = fields.Many2one('ps.mrp.cost.accounting', 'Mrp Cost Accounting')
    name = fields.Char('Reference')
    product_qty = fields.Float(
        'Quantity To Produce', digits=dp.get_precision('Product Unit of Measure'))
    product_inventory_qty = fields.Float(string='Inventory QTY', digits=dp.get_precision('Product Unit of Measure'))
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Picking Type')
    picking_type_name = fields.Char(string='Operation Type')
    state = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='Mrp State')
    period_id = fields.Many2one('ps.account.period', string='Account Period')  # 期间



class PsMrpExpenseDistribution(models.Model):
    _name = 'ps.mrp.expense.distribution'

    period = fields.Char(string='Period')
    name = fields.Char('Reference')
    date = fields.Datetime('Business date')
    mrp_cost_accounting_id = fields.Many2one('ps.mrp.cost.accounting', 'Mrp Cost Accounting')
    cost_item_id = fields.Many2one('ps.mrp.cost.item', string='Cost Item')
    expense_item_id = fields.Many2one('ps.mrp.expense.item', string='Expense Item')
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])],
        readonly=True, required=True,
        states={'confirmed': [('readonly', False)]})
    amount = fields.Float(string='Amount', digits=(16, 2))