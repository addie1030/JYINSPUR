# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ContractSales(models.TransientModel):
    _name = "ps.credit.confirm.wizard"
    _description = 'Wizard sales order credit check'

    name = fields.Char()
    customer_id = fields.Many2one("res.partner", string="Customer")
    amount_total = fields.Float()
    balance = fields.Float()
    order = fields.Many2one('sale.order')
    message = fields.Text()

    @api.multi
    def continue_sale(self):
        '''
        After clicking ok, Continue the sales order
        '''
        sale_order = self.env['sale.order'].search([('id','=',self.order.id)])
        return sale_order.with_context(continue_sale=True).action_confirm()


class StockCheck(models.TransientModel):
    _name = "ps.credit.confirm.stock.wizard"
    _description = 'Wizard stock credit check'

    name = fields.Char()
    customer_id = fields.Many2one("res.partner", string="Customer")
    amount_total = fields.Float()
    balance = fields.Float()
    pick_id = fields.Many2one('stock.picking')
    message = fields.Text()

    @api.multi
    def continue_move(self):
        '''
        After clicking ok, Continue the stock move
        '''
        stock_picking = self.env['stock.picking'].search([('id','=',self.pick_id.id)])
        return stock_picking.with_context(continue_sale=True).button_validate()


