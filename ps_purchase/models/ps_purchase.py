from odoo import fields, models, api, _

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    #确认订单时生成库存单据
    @api.multi
    def _create_stock_moves(self, picking):
        done = super(PurchaseOrderLine, self)._create_stock_moves(picking)
        for order in self:
            for line in done:
                if 'ps_order_price' in line and line.product_id == order.product_id:
                    line.update({'ps_order_price': order.price_unit})

        return done


    ps_date_done = fields.Datetime(string='Date Done', compute='_compute_date_done')

    def _compute_date_done(self):
        """
        获取添加字段ps_date_done，计算字段，取对应的picking中的date_done
        :return:
        """
        for line in self:
            move_ids = self.env['stock.move'].search([('purchase_line_id', '=', line.id)])
            last_date_done = ''
            for move_id in move_ids:
                if not last_date_done or (move_id.picking_id.date_done and move_id.picking_id.date_done > last_date_done):
                    last_date_done = move_id.picking_id.date_done
            line.ps_date_done = last_date_done
