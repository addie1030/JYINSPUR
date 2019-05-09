# -*- coding: utf-8 -*-

import time
import math

from datetime import datetime
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools
from odoo.addons import decimal_precision as dp


class PsPurchaseStockVerification(models.TransientModel):
    _name = 'ps.purchase.stock.verification'

    partner_id = fields.Many2one('res.partner', string=_('Partner'))
    name = fields.Char(string=_('Invoice Stock Move Validate'), default=lambda self: _('Invoice Stock Move Validate'))
    ps_stock_move_ids = fields.One2many('ps.stock.move.line.view', 'ps_verification_id')
    ps_account_invoice_ids = fields.One2many('ps.account.invoice.line.view', 'ps_verification_id')
    stock_move_type = fields.Selection([('in', _('Receipts')), ('out', _('Delivery Orders'))], string=_('Operation Type'))

    @api.multi
    def refresh_data(self):
        self.ensure_one()
        if not self.stock_move_type:
            raise ValidationError(_('Please select operation type.'))  # 请单据类型--in入库单，out出库单
        if not self.partner_id:
            raise ValidationError(_('Please select partner.'))  # 请选择合作伙伴
        if self.ps_stock_move_ids:
            self.ps_stock_move_ids.unlink()
        if self.ps_account_invoice_ids:
            self.ps_account_invoice_ids.unlink()

        if self.stock_move_type == 'in':
            account_invoice_type = 'in_invoice'
            strfilter = 'IN'
        else:
            account_invoice_type = 'out_invoice'
            strfilter = 'OUT'

        sql = """Select t1.origin ,date(t1.date),
                         t2.product_id,
                         t2.quantity,t2.price_unit,
                         t2.price_subtotal,t2.ps_uncancelled_quantity,
                         t2.ps_cancelled_quantity,t2.id
                 From account_invoice t1, account_invoice_line t2
                 Where t1.id = t2.invoice_id and 
                      t1.type = '%s' and
                      t1.state = 'open' and 
                      t2.ps_uncancelled_quantity > 0 and
                      t1.partner_id = %s
                 Order By t2.id
                		 """ % (account_invoice_type, self.partner_id.id)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        if temp_ids:
            item_data = []
            for item in temp_ids:
                item_data.append((0, 0, {
                    'ps_origin': item[0],
                    'ps_date': item[1],
                    'ps_product_id': item[2],
                    'ps_quantity': item[3],
                    'ps_price_unit': item[4],
                    'ps_price_subtotal': item[5],
                    'ps_uncancelled_quantity': item[6],
                    'ps_cancelled_quantity': item[7],
                    'ps_invoice_line_id': item[8]
                }))
            self.ps_account_invoice_ids = item_data

        # 刷新库存单据

        sql = """Select t1.reference,t1.origin,
                        date(t1.date),
                        t1.product_id,t1.product_qty,
                        t1.price_unit,t1.value,
                        t1.ps_uncancelled_quantity,t1.ps_cancelled_quantity,
                        t1.id
                From stock_move t1, stock_picking t2
                Where t1.picking_id = t2.id and 
                      t1.reference like  '%%%%%s%%%%' and
                      t1.state = 'done' and
                      t1.ps_uncancelled_quantity > 0 and 
                      t2.partner_id = %s
                Order By t1.id
                        		 """ % (strfilter, self.partner_id.id)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        if temp_ids:
            item_data = []
            for item in temp_ids:
                item_data.append((0, 0, {
                    'ps_ref': item[0],
                    'ps_origin': item[1],
                    'ps_date': item[2],
                    'ps_product_id': item[3],
                    'ps_quantity': item[4],
                    'ps_price_unit': item[5],
                    'ps_price_subtotal': item[6],
                    'ps_uncancelled_quantity': item[7],
                    'ps_cancelled_quantity': item[8],
                    'ps_stock_move_id': item[9]
                }))
            self.ps_stock_move_ids = item_data
        return True


class PsStockMoveLineView(models.TransientModel):
    _name = 'ps.stock.move.line.view'

    ps_stock_move_id = fields.Integer(string=_('StockID'))
    ps_ref = fields.Char(string=_('Document Number'))  # 入库单号
    ps_origin = fields.Char(string=_('Source Document'))  # 订单号
    ps_date = fields.Date(string=_('Business Date'))  # 业务日期
    ps_partner_id = fields.Many2one('res.partner', string=_('Supplier'))  # 供应商
    ps_product_id = fields.Many2one('product.product', string=_('Product'))  # 产品
    ps_quantity = fields.Float(string=_('Quantity'), digits=dp.get_precision('Product Unit of Measure'))  # 数量
    ps_price_unit = fields.Float(string=_('Unit Price'), digits=dp.get_precision('Product Price'))  # 单价
    ps_price_subtotal = fields.Float(string=_('Amount'), digits=dp.get_precision('Account'))  # 金额
    ps_cancelled_quantity = fields.Float(string=_('Cancelled Quantity'), default=0,
                                         digits=dp.get_precision('Product Unit of Measure'))  # 核销数量
    ps_uncancelled_quantity = fields.Float(string=_('Uncancelled Quantity'),
                                           digits=dp.get_precision('Product Unit of Measure'))  # 未核销数量
    ps_the_cancelled_quantity = fields.Float(string=_('The Cancelled Quantity'),
                                             digits=dp.get_precision('Product Unit of Measure'))  # 本次核销数量
    ps_verification_id = fields.Many2one('ps.purchase.stock.verification', ondelete="cascade")


class PsStockMove(models.Model):
    _inherit = 'stock.move'

    ps_uncancelled_quantity = fields.Float(string=_('Uncancelled Quantity'),
                                           compute='compute_ps_uncancelled_quantity',
                                           store=True)  # 未核销数量
    ps_cancelled_quantity = fields.Float(string=_('Cancelled Quantity'), default=0)  # 核销数量
    ps_the_cancelled_quantity = fields.Float(string=_('The Cancelled Quantity'))  # 本次核销数量
    ps_validate_amount = fields.Float(string=_('Validate Amount'))

    @api.depends('product_qty', 'ps_cancelled_quantity')
    def compute_ps_uncancelled_quantity(self):
        for r in self:
            r.ps_uncancelled_quantity = r.product_qty - r.ps_cancelled_quantity


class PsAccountInvoiceLineView(models.TransientModel):
    _name = 'ps.account.invoice.line.view'

    ps_invoice_line_id = fields.Integer(string=_('InvoiceID'))
    ps_origin = fields.Char(string=_('Source Document'))  # 订单号
    ps_date = fields.Date(string=_('Business Date'))  # 业务日期
    ps_partner_id = fields.Many2one('res.partner', string=_('Supplier'))  # 供应商
    ps_product_id = fields.Many2one('product.product', string=_('Product'))  # 产品
    ps_quantity = fields.Float(string=_('Quantity'), digits=dp.get_precision('Product Unit of Measure'))  # 数量
    ps_price_unit = fields.Float(string=_('Unit Price'))  # 单价
    ps_price_subtotal = fields.Float(string=_('Amount'))  # 金额
    ps_cancelled_quantity = fields.Float(string=_('Cancelled Quantity'), default=0)  # 核销数量
    ps_uncancelled_quantity = fields.Float(string=_('Uncancelled Quantity'))  # 未核销数量
    ps_verification_id = fields.Many2one('ps.purchase.stock.verification', ondelete="cascade")


class PsAccountInvoice(models.Model):
    _inherit = 'account.invoice.line'

    ps_uncancelled_quantity = fields.Float(string=_('Uncancelled Quantity'),
                                           compute='compute_ps_uncancelled_quantity',
                                           store=True)  # 未核销数量
    ps_cancelled_quantity = fields.Float(string=_('Cancelled Quantity'))  # 核销数量

    @api.depends('quantity', 'ps_cancelled_quantity')
    def compute_ps_uncancelled_quantity(self):
        for r in self:
            r.ps_uncancelled_quantity = r.quantity - r.ps_cancelled_quantity


class PsInvoiceLineStockMoveRecs(models.Model):
    _name = 'ps.invoice.line.stock.move.recs'

    invoice_line_id = fields.Many2one('account.invoice.line')
    invoice_line_qty = fields.Float(digits=(16, 2))
    invoice_line_validate_qty = fields.Float(digits=(16, 2))
    invoice_line_validate_value = fields.Float(digits=(16, 2))
    stock_move_id = fields.Many2one('stock.move')
    stock_move_qty = fields.Float(digits=(16, 2))
    stock_move_validate_qty = fields.Float(digits=(16, 2))
    stock_move_validate_value = fields.Float(digits=(16, 2))
    operation_date = fields.Date()
    move_id = fields.Many2one('account.move')
    origin = fields.Selection([('in', _('Receives')), ('out', _('Delivery Orders'))], string=_('Origin'))


class PsResCompany(models.Model):
    _inherit = 'res.company'

    cogs_account_id = fields.Many2one('account.account', string='COGS Account',
                                                  domain=[('deprecated', '=', False)],
                                                  company_dependent=True)
