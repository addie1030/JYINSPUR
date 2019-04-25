# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    ps_date_done = fields.Datetime(string='Date Done', compute='_compute_date_done')

    def _compute_date_done(self):
        """
        获取添加字段ps_date_done，计算字段，取对应的picking中的date_done
        :return:
        """
        for line in self:
            move_ids = self.env['stock.move'].search([('sale_line_id', '=', line.id)])
            last_date_done = ''
            for move_id in move_ids:
                if not last_date_done or (move_id.picking_id.date_done > last_date_done):
                    last_date_done = move_id.picking_id.date_done
            line.ps_date_done = last_date_done

    @api.model
    def write(self, vals):
        """
        修改销售订单数量少于原订单数量时，同步更新到stock.picking明细（stock.move）中的Initial Demand和Reserved数量
        :param vals:
        :return:
        """
        if 'product_uom_qty' in vals:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(self.product_uom_qty, vals['product_uom_qty'], precision_digits=precision) >= 0:
                if self.state == 'sale' or not self.product_id.type not in ('consu', 'product'):
                    domain = [('sale_line_id', '=', self.id), ('state', 'not in', ['done','cancel'])]
                    stock_move = self.env['stock.move'].search(domain)
                    if stock_move:
                        stock_move.product_uom_qty = vals['product_uom_qty'] - self.qty_delivered
                        stock_move.picking_id.do_unreserve()
                        stock_move.picking_id.action_assign()
        return super(SaleOrderLine, self).write(vals)

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        # When modifying a one2many, _origin doesn't guarantee that its values will be the ones
        # in database. Hence, we need to explicitly read them from there.
        return {}
