# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression


class ProductTicCategory(models.Model):
    _name = 'product.tic.category'
    _description = "Product TIC Category"
    _rec_name = 'code'

    code = fields.Integer(string="TIC Category Code", required=True)
    description = fields.Char(string='TIC Description', required=True)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        tic_category_ids = []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('description', operator, name), ('code', operator, name)]
        tic_category_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(tic_category_ids).name_get()

    @api.multi
    def name_get(self):
        res = []
        for category in self:
            res.append((category.id, _('[%s] %s') % (category.code, category.description[0:50])))
        return res

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tic_category_id = fields.Many2one('product.tic.category', string="TaxCloud Category",
        help="Each product falls into a category which has specific taxes predermined by the government."
            "The system will use the Tax Cloud category set on the internal category of the product. If there"
            "isn't any, the one on the product itself will be used. Only used in United States.")

class ResCompany(models.Model):
    _inherit = 'res.company'

    tic_category_id = fields.Many2one('product.tic.category', string='Default TIC Code', help="Default TICs(Taxability information codes) code to get sales tax from TaxCloud by product category.")

class ProductCategory(models.Model):
    _inherit = "product.category"

    tic_category_id = fields.Many2one('product.tic.category', string='TIC Code',
        help="TaxCloud uses Taxability Information Codes (TIC) to make sure each item in your catalog "
             "is taxed at the right rate (or, for tax-exempt items, not taxed at all), so it's important "
             "to make sure that each item is assigned a TIC. If you can't find the right tax category for "
             "an item in your catalog, you can assign it to the 'General Goods and Services' TIC, 00000. "
             "TaxCloud automatically assigns products to this TIC as a default, so unless you've changed an "
             "item's TIC in the past, it should already be set to 00000.")
