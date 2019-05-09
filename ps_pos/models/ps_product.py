# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

class PsProduct(models.Model):
    _inherit = "stock.quant"

    @api.model
    def judging_excess(self, newarr, companyid):
        for arr in newarr:
            res = self.search([('product_id', '=', arr[1]), ('company_id', '=', companyid)])
            if res:
                if arr[0] > res.quantity:
                    return False, res.quantity, res.product_id.name
        return True