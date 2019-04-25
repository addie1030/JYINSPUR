from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _action_launch_stock_rule(self):
        result = super(SaleOrderLine, self)._action_launch_stock_rule ()
        for order in self:
            for line in order.move_ids:
                if 'ps_order_price' in line and line.product_id == order.product_id:
                    line.update({'ps_order_price': order.price_unit})
        return result
