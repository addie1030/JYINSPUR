# -*- coding: utf-8 -*-
import logging
from odoo import api, exceptions, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, pycompat
from odoo.osv.orm import setup_modifiers
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime

_logger = logging.getLogger(__name__)

class PsPurchaseOrderChange(models.Model):
    _name = "ps.purchase.order.change"
    _description = 'Purchase Change Order'
    _sql_constraints = [
        ('document_code_unique', 'unique(name)', 'Document number cannot be repeated')]

    name = fields.Char(string='Document No.', requried=True)#单据编号
    date = fields.Date(string='Document Date', required=True, default=fields.Date.today)#单据日期
    change_date = fields.Date(string='Date of Change', required=True, default=fields.Date.today)#变更日期
    user_id = fields.Many2one('res.users', string='Changer', default=lambda self: self.env.user)#变更人
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Document State', index=True, required=True, default='draft',
    help="Defines the state of the purchase change order.")#状态
    change_reason = fields.Char(string='Change Reason', required=True)#变更原因
    order_id = fields.Many2one('purchase.order', string='Origin Purchase Order')#源采购订单
    partner_id = fields.Many2one('res.partner', string='Vendor', related='order_id.partner_id', readonly=True, store=True)#供应商
    partner_ref = fields.Char(string='Vendor Reference', related='order_id.partner_ref', readonly=True, store=True)#供应商参照
    currency_id = fields.Many2one('res.currency', string='Currency', related='order_id.currency_id', readonly=True, store=True)#币种
    company_id = fields.Many2one('res.company', string='Company', related='order_id.company_id', readonly=True, store=True)#公司
    change_line_ids = fields.One2many('ps.purchase.order.change.line', 'order_change_id', string='Purchase Order Change Line')#变更明细
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')

    @api.constrains('change_line_ids','change_reason')
    def _check_whether_change_line_ids_zero(self):
        for line in self:
            if len(line.change_line_ids) == 0:
                raise ValidationError(_('There no change lines in this order, could not be saved'))

    @api.depends('change_line_ids.price_total', 'change_line_ids.price_unit', 'change_line_ids.product_qty')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.change_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ps.purchase.order.change')
        return super(PsPurchaseOrderChange, self).create(vals)

    @api.multi
    def unlink(self):
        for r in self:
            if r.state == 'confirmed':
                raise ValidationError(_('The change order ') + r.name + _(' is confirmed, can not be deleted.'))
        return super(PsPurchaseOrderChange, self).unlink()

    @api.multi
    def button_confirm(self):
        self.ensure_one()
        self.write({'state': 'confirmed'})
        # 将改变的数据写入原采购订单
        purchase_lines = self.env['purchase.order.line'].search([('order_id','=', self.order_id.id)])
        purchase_id = []
        purchase_ids = []
        for r in self.change_line_ids:
            for line in purchase_lines:
                purchase_ids.append(line.id)
                if r.order_line_id == line:
                    line.write({
                        'product_qty': r.product_qty,
                        'price_unit' : r.price_unit,
                    })
        #获取与入库相关的采购明细
        for id in purchase_ids:
            if id not in purchase_id:
                purchase_id.append(id)
        move_lines = self.env['stock.move'].search(
            [('purchase_line_id', 'in', purchase_id), ('state', '=', 'assigned')])
        # 将改变的数据写入相应的入库单
        for r in self.change_line_ids:
            for line in move_lines:
                if r.order_line_id == line.purchase_line_id:
                    line.write({
                        'product_uom_qty': r.product_qty-r.qty_received,
                        'price_unit' : r.price_unit,
                    })
                    if 'ps_order_price' in line:
                        line.write({'ps_order_price': r.price_unit})

    @api.onchange('order_id')
    def _refresh_data(self):
        """
        根据原采购订单，获取其相应的采购订单明细信息，填写到变更明细表中，部分采购订单根据条件限制不可选择
        """
        self.ensure_one()
        line_ids = self.env['purchase.order.line'].search([('order_id', '=', self.order_id.id)])
        precision_qty = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        # 欠单的相关处理
        if self.order_id:
            move_ids = self.env['stock.move'].search([('group_id', '=', self.order_id.group_id.id)])
            for move in move_ids:
                if move.state == 'cancel' and move.picking_id.backorder_id:
                    raise ValidationError(_('This order did not create backorder and thus cannot be changed.'))
        item_data = []
        #如果采购单的产品已全部接收，则此订单无法选择
        if self.order_id and sum([float_compare(r.product_qty, r.qty_received, precision_digits=precision_qty) for r in line_ids]) == 0:
            raise ValidationError(_('All products in this order has been completely received and thus cannot be changed.'))
        for line in line_ids:
            if float_compare(line.product_qty, line.qty_received, precision_digits=precision_qty) != 0:#采购明细行如已全部接收则不写入
                item_data.append(
                    {'product_id' : line.product_id,
                    'order_line_id' : line.id,
                    'pre_product_qty' : line.product_qty,
                    'pre_price_unit': line.price_unit,
                    'product_qty' : line.product_qty,
                    'price_unit' : line.price_unit,
                     }
                )
        self.change_line_ids = item_data

class PsPurchaseOrderChangeLine(models.Model):
    _name = "ps.purchase.order.change.line"
    _description = 'Purchase Change Order Line'

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(line.price_unit, line.order_change_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_change_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    order_change_id = fields.Many2one('ps.purchase.order.change', string='Purchase Change Order', ondelete='cascade')#变更单
    order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')#源采购明细
    product_id = fields.Many2one('product.product', string='Product')#产品
    name = fields.Text(string='Description', related='order_line_id.name', store=True, readonly=True)#说明
    sequence = fields.Integer(string='Sequence', related='order_line_id.sequence', store=True, readonly=True)#序列
    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                related='order_line_id.taxes_id', readonly=True)#税率
    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related='order_line_id.product_uom',
        help="This comes from the purchase order line.", store=True, readonly=True)#计量单位
    pre_product_qty = fields.Float(string='Original Quantity', digits=dp.get_precision('Product Unit of Measure'))#变更前数量
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))#数量(变更后)
    pre_price_unit = fields.Float(string='Original Unit Price', digits=dp.get_precision('Product Price'))#变更前单价
    price_unit = fields.Float(string='Unit Price', digits=dp.get_precision('Product Price'))#单价(变更后)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)#小计
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)#总计
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)#税额
    company_id = fields.Many2one('res.company', string='Company', related='order_line_id.order_id.company_id', readonly=True)#公司
    state = fields.Selection(related='order_change_id.state', store=True)#状态
    qty_invoiced = fields.Float(string="Billed Qty", related='order_line_id.qty_invoiced',
                                digits=dp.get_precision('Product Unit of Measure'), store=True, readonly=True)#开票数量
    qty_received = fields.Float(string="Received Qty", related='order_line_id.qty_received',
                                digits=dp.get_precision('Product Unit of Measure'), store=True, readonly=True)#接收数量
    partner_id = fields.Many2one('res.partner', string='Vendor', related='order_line_id.order_id.partner_id', readonly=True)#供应商
    currency_id = fields.Many2one('res.currency', string='Currency', related='order_line_id.order_id.currency_id', readonly=True)#币种

    @api.constrains('product_qty','price_unit')
    def _check_whether_qty_or_price_changes(self):
        precision_price = self.env['decimal.precision'].precision_get('Product Price')
        precision_qty = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for r in self:
            if float_compare(r.price_unit, r.pre_price_unit, precision_digits=precision_price) == 0 and \
                    float_compare(r.product_qty, r.pre_product_qty, precision_digits=precision_qty) == 0:
                raise ValidationError(_('The record containing ') + r.name + _(' has nothing different with the former one'))

    @api.constrains('product_qty')
    def _check_whether_changed_qty_less_than_qty_received(self):
        for r in self:
            if r.product_qty < r.qty_received:
                raise ValidationError(_("The changed quantity must larger than quantity received."))