# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError, Warning


class StockMove(models.Model):
    _inherit = "stock.move"

    ps_order_price = fields.Float(string='Order Price', digits=dp.get_precision('Product Price')
                                  , group_operator="avg")#订单价格
    ps_order_amount = fields.Float(string='Complete Order Amount', digits=dp.get_precision('Product Price'),
                                   compute='_set_ps_order_amount', store=True)#完成订单金额

    @api.multi
    @api.depends('move_line_ids.qty_done', 'move_line_ids.product_uom_id', 'move_line_nosuggest_ids.qty_done', 'ps_order_price')
    def _set_ps_order_amount(self):
        for line in self:
            line.ps_order_amount = line.ps_order_price * line.quantity_done


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _ps_purchase_over_return_config_param(self, moves_in_order):
        products_in_order = []
        # 获取同一源单据上所有的产品种类，并确认退回数量的增减方向
        for move in moves_in_order:
            if move.purchase_line_id and move.product_id.id not in products_in_order:
                move_direction_plus = 'incoming'
                move_direction_minus = 'outgoing'
                products_in_order.append(move.product_id.id)
        return products_in_order, move_direction_plus, move_direction_minus


    def _ps_sale_over_return_config_param(self, moves_in_order):
        products_in_order = []
        # 获取同一源单据上所有的产品种类，并确认退回数量的增减方向
        for move in moves_in_order:
            if move.sale_line_id and move.product_id.id not in products_in_order:
                move_direction_plus = 'outgoing'
                move_direction_minus = 'incoming'
                products_in_order.append(move.product_id.id)
        return products_in_order, move_direction_plus, move_direction_minus

    def _create_returns(self):
        new_picking, pick_type_id = super(ReturnPicking, self)._create_returns()
        self.ensure_one()
        res_purchase = self.picking_id.company_id.ps_is_overpass_initial_ordered_process if 'ps_is_overpass_initial_ordered_process' in self.picking_id.company_id else False
        res_sale = self.picking_id.company_id.ps_is_overpass_initial_ordered_sale if 'ps_is_overpass_initial_ordered_sale' in self.picking_id.company_id else False
        if res_purchase or res_sale:
            # 获取来自同一源单据的所有库存移动记录
            moves_in_order = self.env['stock.move'].search([('group_id', '=', self.picking_id.group_id.id)])
            return_list = []
            # 计算每一种产品的剩余数量
            if res_purchase and sum([move.purchase_line_id.id for move in moves_in_order]) != 0:
                products_in_order, move_direction_plus, move_direction_minus \
                    = self._ps_purchase_over_return_config_param(moves_in_order)
            elif res_sale and sum([move.sale_line_id.id for move in moves_in_order]) != 0:
                products_in_order, move_direction_plus, move_direction_minus \
                    = self._ps_sale_over_return_config_param(moves_in_order)
            for product_id in products_in_order:
                return_qty = 0
                for move in moves_in_order:
                    if move.picking_type_id.code == move_direction_plus and move.product_id.id == product_id and move.state != 'cancel':
                        return_qty += move.product_qty
                    elif move.picking_type_id.code == move_direction_minus and move.product_id.id == product_id and move.state != 'cancel':
                        return_qty += -move.product_qty
                return_list.append(return_qty)
            # 如果任意产品的退货数量超过源单据
            for remain_qty in return_list:
                if remain_qty < 0:
                    raise UserError(_("The quantity of returns cannot be more than that in source document."))
        return new_picking, pick_type_id