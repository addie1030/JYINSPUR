# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    ps_trade_name = fields.Char(string='trade-name')#商品名称

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ps_trade_name = fields.Char(string='trade-name')  # 商品名称
    ps_specification = fields.Char(string='specification')  # 规格型号

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        res = self.env['product.category'].search([('id', '=', self.categ_id.id)])
        if res:
            self.ps_trade_name = res.ps_trade_name

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        res = self.env['product.category'].search([('id', '=', self.categ_id.id)])
        if res:
            self.ps_trade_name = res.ps_trade_name
