# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cash_id = fields.Many2one(comodel_name='ps.core.value', string='The cash flow statement ')
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string="vehicle ")
    product_id = fields.Many2one(comodel_name='product.product', string="product ")
    quantity = fields.Float(string="The number of ")
    product_per_price = fields.Float(string="The unit price ")


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    before_im_deprecaited = fields.Float(string='Before the import accumulated depreciation ' )
    before_im_value = fields.Float(string='Before the import net ' )
    fleet_id = fields.Many2one(comodel_name='fleet.vehicle', string="vehicle ")
    purchase_time = fields.Date(string='Purchase date ', states={'draft': [('readonly', False), ('required', True)]})
    origin_value = fields.Float(string='Original value of fixed assets ')