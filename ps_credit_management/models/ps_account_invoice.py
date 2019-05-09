# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    ps_picking_id = fields.Many2one('stock.picking', string="Stock Picking")

    def _get_invoice_line_name_from_product(self, product_id):
        """ Returns the automatic name to give to the invoice line depending on
        the product it is linked to.
        """
        self.ensure_one()

        invoice_type = self.type
        rslt = product_id.partner_ref
        if invoice_type in ('in_invoice', 'in_refund'):
            if product_id.description_purchase:
                rslt += '\n' + product_id.description_purchase
        else:
            if product_id.description_sale:
                rslt += '\n' + product_id.description_sale

        return rslt

    @api.onchange('ps_picking_id')
    def onchange_ps_picking(self):
        """
        当为出库单开发票时，选择出库单之后，自动带出出库明细
        :return:
        """
        values = []
        if self.ps_picking_id:
            part = self.partner_id

            self_lang = self
            if part.lang:
                self_lang = self.with_context(lang=part.lang)

            move_ids = self.env['stock.move'].search([('picking_id', '=', self.ps_picking_id.id)])
            if move_ids:
                for move_id in move_ids:
                    product_name = self_lang._get_invoice_line_name_from_product(move_id.product_id)
                    val = (0, 0,
                           {
                               'product_id': move_id.product_id.id,
                               'name': product_name if product_name else move_id.product_id.name,
                               'quantity': self.env['stock.move.line'].search(
                                   [('move_id', '=', move_id.id)]).qty_done - move_id.ps_invoice_qty,
                               'price_unit': move_id.ps_stock_price,
                               'ps_picking_id': self.ps_picking_id.id,
                               'ps_move_id': move_id.id,
                               'account_id': move_id.product_id.categ_id.property_account_income_categ_id.id,
                               'invoice_line_tax_ids': [(6, 0, move_id.product_id.taxes_id.ids)]
                           })
                    values.append(val)
            else:
                values=False
            self.invoice_line_ids = values


class AccountInvoiceline(models.Model):
    _inherit = 'account.invoice.line'

    ps_picking_id = fields.Many2one('stock.picking', string="Stock Picking")
    ps_move_id = fields.Many2one('stock.move', string="Stock Move")


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(
                        product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            if pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = product_currency or (
                product.company_id and product.company_id.currency_id) or self.env.user.company_id.currency_id
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id,
                                                              self.order_id.date_order)

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

    def _compute_outgoing_price(self):
        """
        根据客户价格表计算产品的销售价格
        :return:
        """
        for self in self:
            if self.picking_id.partner_id.property_product_pricelist:
                product = self.product_id.with_context(
                    lang=self.picking_id.partner_id.lang,
                    partner=self.picking_id.partner_id,
                    quantity=self.product_uom_qty,
                    date=self.date_expected,
                    pricelist=self.picking_id.partner_id.property_product_pricelist.id,
                    uom=self.product_uom.id,
                    fiscal_position=self.env.context.get('fiscal_position')
                )

                product_context = dict(self.env.context, partner_id=self.picking_id.partner_id.id,
                                       date=self.date_expected,
                                       uom=self.product_uom.id)

                price, rule_id = self.picking_id.partner_id.property_product_pricelist.with_context(
                    product_context).get_product_price_rule(
                    self.product_id, self.product_uom_qty or 1.0, self.picking_id.partner_id)
                new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                                       self.product_uom_qty,
                                                                                                       self.product_uom,
                                                                                                       self.picking_id.partner_id.property_product_pricelist.id)
            else:
                new_list_price = self.product_id.lst_price
            self.ps_stock_price = new_list_price

    ps_stock_price = fields.Float(string="Stock Price", compute=_compute_outgoing_price)
    ps_invoice_qty = fields.Integer(string="Invoice Qty", compute="compute_invoice_qty")
    ps_invoice_account = fields.Integer(string="Invoice Qty", compute="compute_invoice_qty")

    def compute_invoice_qty(self):
        """
        计算发票来源为出库单的开票数量
        :return:
        """
        for self in self:
            self.ps_invoice_qty = 0
            invoice_line_id = self.env['account.invoice.line'].search(
                [('ps_picking_id', '=', self.picking_id.id), ('ps_move_id', '=', self.id)])
            if invoice_line_id.invoice_id.state == 'paid':
                self.ps_invoice_qty = invoice_line_id.quantity
            qty_done = self.env['stock.move.line'].search([('move_id', '=', self.id)]).qty_done
            self.ps_invoice_account = self.ps_invoice_qty * qty_done
