# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PsPriceListProduct(models.Model):
    _inherit = 'product.pricelist'

    ps_product_ids = fields.Many2many('product.template', string='Product', compute='_compute_product_name')

    @api.model
    def _compute_product_name(self):
        product_list_ids = self.env['product.pricelist.item'].search([('pricelist_id', '=', self.id)])
        product_ids = []
        for product_list in product_list_ids:
            product_ids.append(product_list.product_tmpl_id.id)
        self.ps_product_ids = [(6, 0, product_ids)]
