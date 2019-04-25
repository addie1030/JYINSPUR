# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError, Warning


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.constrains('quantity_done', 'product_uom_qty')
    def _check_ps_overpass_sale_and_return(self):
        self.ensure_one()
        res = self.company_id.ps_is_overpass_initial_ordered_sale
        if res and self.sale_line_id and self.quantity_done > self.product_uom_qty:
            raise ValidationError(
                _('Selling/Returning more than what was initially planned for the product is not allowed.'))
