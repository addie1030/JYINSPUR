# -*- coding: utf-8 -*-
import time

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleContract(models.Model):
    _name = 'ps.sale.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ps sale contract'

    name = fields.Char(string='Name', default=lambda self: _('New'), copy=False)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    invoice_address_id = fields.Many2one('res.partner', string='Invoice Address',
                                         domain=[('type', '=', 'invoice')])
    customer_id = fields.Many2one('res.partner', string='Customer', change_default=True, index=True,
                                  track_visibility='always',
                                  track_sequence=1,
                                  help="You can find a customer by its Name, TIN, Email or Internal Reference.")
    customer_representative_id = fields.Many2one('res.partner', string='Customer Representative')
    date_confirmed = fields.Datetime(string='Date Confirmed')
    amount_tax = fields.Float(string='Amount Tax', compute='_compute_amount_all')
    amount_untaxed = fields.Float(string='Amount Untax', compute='_compute_amount_all')
    amount = fields.Float(string='Amount', compute='_compute_amount_all')
    is_invoice = fields.Boolean("? is invoice", compute="compute_amount_deliveried")
    sale_person_id = fields.Many2one('res.users', string='Sale Person')
    sale_team_id = fields.Many2one('crm.team', string='Sale Team')
    amount_deliveried = fields.Float(string='Amount Deliveried')
    amount_ordered = fields.Float(string='Amount Ordered')
    valid_to = fields.Date(string='Valid To', compute='_compute_valid_to')
    valid_from = fields.Date(string='Valid From')
    valid_days = fields.Integer(string='Valid Days')
    amount_prepaid = fields.Float(string='Amount Prepaid', store=True)
    paid_amount_prepaid = fields.Float(string="Paid Amount Prepaid", compute='_compute_paid_amount')
    state = fields.Selection([('draft', "Draft"),
                              ('confirmed', "Confirmed"),
                              ('approved', "Approved"),
                              ('closed', "Closed"),
                              ('cancelled', "Cancelled")], string='Status', default='draft',
                             index=True, track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', related="pricelist_id.currency_id", string='Currency')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id.id)
    line_ids = fields.One2many('ps.sale.contract.line', 'contract_id', string='Line')
    term_ids = fields.Many2many('ps.sale.contract.term', string='Term')
    sale_order_line_ids = fields.Many2many('sale.order.line', string='Sale Order Line')
    stock_move_ids = fields.Many2many('stock.move', string='Stock Move')
    sale_order_ids = fields.Many2many('sale.order', string='Sale Order')
    stock_picking_ids = fields.Many2many('stock.picking', string='Stock Picking')
    order_count = fields.Integer(string='Orders', compute='_compute_order_ids')
    delivery_count = fields.Integer(string='Delivery', compute='_compute_order_ids')
    invoice_count = fields.Integer(string='Invoices', compute='_compute_order_ids')
    invoice = fields.Char(string='Invoice')
    order = fields.Char(string='Order')
    delivery = fields.Char(string='Delivery')
    order_remaining = fields.Boolean(compute="compute_amount_deliveried")
    is_reconciled = fields.Boolean(compute="compute_amount_deliveried")
    is_expired = fields.Boolean(compute="compute_is_expired")

    def compute_amount_deliveried(self):
        order_remaining = False
        for self in self:
            self.amount_deliveried = 0.0
            self.is_invoice = False
            self.order_finish = False
            pre_payment = self.env['account.payment'].search([('communication', '=', self.name)], limit=1)
            if pre_payment:
                if pre_payment.state == 'posted':
                    self.is_reconciled = True
            else:
                self.is_reconciled = True
            sale_orders = self.env['sale.order'].search(
                [('contract_id', '=', self.id)])
            for sale_order in sale_orders:
                invoices = self.env['account.invoice'].search(
                    [('origin', '=', sale_order.name)])
                for invoice in invoices:
                    if invoice:
                        if invoice.state != 'draft':
                            self.is_invoice = True
                    else:
                        self.is_invoice = True

            for line in self.line_ids:
                if line.qty_ordered - line.quantity < 0:
                    order_remaining = True
        self.order_remaining = order_remaining


    def _compute_paid_amount(self):
        payment = self.env["account.payment"].search([("communication", "=", self.name), ("state", "!=", 'draft')],
                                                    limit=1)
        self.paid_amount_prepaid = payment.amount

    def compute_is_expired(self):
        currentdate = fields.Date.today()
        if self.valid_from > currentdate or currentdate > self.valid_to:
            self.is_expired = True

    @api.multi
    @api.onchange('customer_id')
    def onchange_customer_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Invoice Address
        """
        if not self.customer_id:
            self.update({
                'invoice_address_id': False,
                'pricelist_id': False,
                'customer_representative_id': False
            })
        else:
            addr = self.customer_id.address_get(['delivery', 'invoice'])
            customer_representative_id = self.env['res.partner'].search(
                [('type', '=', 'contact'), ('parent_id', '=', self.customer_id.id)], limit=1)
            values = {
                'pricelist_id': self.customer_id.property_product_pricelist.id and self.customer_id.property_product_pricelist.id or False,
                'invoice_address_id': addr['invoice'],
                'customer_representative_id': customer_representative_id.id or self.customer_id,
                'sale_person_id': self.customer_id.user_id.id or self.env.uid
            }

            if self.sale_person_id.team_id:
                team_id = self.env['crm.team'].search([('member_ids', '=', self.sale_person_id)], limit=1)
                values['sale_team_id'] = team_id.id
            self.update(values)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code(
                    'ps.sale.contract') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('ps.sale.contract') or _('New')
        self.check_contract_line_ids(vals, 'create')
        return super(SaleContract, self).create(vals)

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if not default.get('line_ids'):
            line_ids = []
            for lines in self.line_ids:
                line_ids.append((0, 0, {
                    'product_id': lines.product_id.id,
                    'quantity': lines.quantity,
                    'contract_id': lines.contract_id,
                    'description': lines.description,
                    'qty_ordered': lines.qty_ordered,
                    'qty_delivered': lines.qty_delivered,
                    'qty_invoiced': lines.qty_invoiced,
                    'uom_id': lines.uom_id,
                    'price': lines.price,
                    'tax_id': lines.tax_id.id,
                    'amount_tax': lines.amount_tax,
                    'subtotal': lines.subtotal,
                    'sale_order_line_ids': lines.sale_order_line_ids,
                    'stock_move_ids': lines.stock_move_ids,
                    'invoice_address_id': lines.invoice_address_id
                }))

            default.update(line_ids=line_ids)
        return super(SaleContract, self).copy(default)

    @api.depends('valid_from', 'valid_days')
    def _compute_valid_to(self):
        '''Automatically calculates the expiration date'''
        for self in self:
            if self.valid_from:
                timeStamp = int(time.mktime(time.strptime(str(self.valid_from), "%Y-%m-%d")))
                timeArray = timeStamp + self.valid_days * 24 * 3600
                self.update({'valid_to': time.strftime("%Y-%m-%d", time.localtime(timeArray))})

    @api.depends('line_ids.amount_tax')
    def _compute_amount_all(self):
        """
        Total taxes, total untaxed amount, total amount
        """
        for order in self:
            if order.line_ids:
                amount_untaxed = amount_tax = 0.0
                for line in order.line_ids:
                    amount_untaxed += line.subtotal
                    amount_tax += line.amount_tax

                order.amount_untaxed = order.pricelist_id.currency_id.round(amount_untaxed)
                order.amount_tax = order.pricelist_id.currency_id.round(amount_tax)
                order.amount = amount_untaxed + amount_tax

    @api.depends('order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
    def _compute_amount_delivery(self):
        for order in self:
            if self.env.user.has_group('sale.group_show_price_subtotal'):
                order.amount_delivery = sum(order.order_line.filtered('is_delivery').mapped('price_subtotal'))
            else:
                order.amount_delivery = sum(order.order_line.filtered('is_delivery').mapped('price_total'))

    @api.depends('sale_order_ids')
    def _compute_order_ids(self):
        for contract in self:
            sale_orders = self.env['sale.order'].search(
                [('contract_id', '=', contract.id)])
            contract.order_count = len(sale_orders)
            delivery_count = 0
            invoice_count = 0
            for order in sale_orders:
                delivery_count += len(order.picking_ids)
                invoice_count += order.invoice_count

            invoice = self.env['account.invoice'].search(
                [('origin', '=', contract.name)])
            if invoice:
                invoice_count += 1
            contract.delivery_count = delivery_count
            contract.invoice_count = invoice_count


    @api.multi
    def action_view_order(self):
        '''
        This function returns an action that display existing sale orders
        of given contract ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('ps_sale_contract.action_orders_all').read()[0]

        orders = self.env['sale.order'].search(
            [('contract_id', '=', self.id)])
        if len(orders) > 1:
            action['domain'] = [('id', 'in', orders.ids)]
        elif orders:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = orders.id
        return action


    @api.multi
    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        orders = self.env['sale.order'].search(
            [('contract_id', '=', self.id)])

        pickings = orders.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action


    @api.multi
    def action_view_invoice(self):
        orders = self.env['sale.order'].search(
            [('contract_id', '=', self.id)])
        invoices = orders.mapped('invoice_ids')
        invoice = self.env['account.invoice'].search(
            [('origin', '=', self.name)])
        invoices = invoices | invoice
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    @api.multi
    def action_submit(self):
        return self.write({'state': 'confirmed'})

    @api.multi
    def action_approve(self):
        self.create_payment()
        self.date_confirmed = fields.Datetime.now()
        return self.write({'state': 'approved'})

    @api.multi
    def create_payment(self):
        payment_obj = self.env['account.payment']
        journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id
        payment_obj.create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.customer_id.id,
            'amount': self.amount_prepaid,
            'payment_method_id': 2,
            'communication': self.name,
            'journal_id': journal_id,
        })


    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})


    @api.multi
    @api.depends('line_ids.qty_delivered', 'line_ids.qty_invoiced')
    def action_close(self):
        '''
        close the contract
        '''
        for line in self.line_ids:
            if line.qty_delivered <= line.qty_invoiced:
                if not self.is_invoice:
                    raise UserError(_("Please confirm all invoice have confirmed"))
                if not self.is_reconciled:
                    payment = self.env['account.payment'].search([('communication', '=', self.name)], limit=1)
                    invoice_origin = payment.communication
                    invoice_amount = payment.amount
                    raise UserError(_("Advances payment(origin:%s,amount:%s) must be reconciled first") % (
                        invoice_origin, invoice_amount))
                else:
                    return self.write({'state': 'closed'})
            else:
                raise UserError(_("Please confirm all invoice have created"))


    @api.multi
    def action_cancel(self):
        return self.write({'state': 'cancelled'})


    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError(_("Don't delete contracts."))
        return super(SaleContract, self).unlink()

    @api.constrains('amount_prepaid')
    def constrains_paid_amount_prepaid(self):
        if self.amount_prepaid < 0:
            raise UserError(_('The amount prepaid can not less than zero.'))
        if self.amount_prepaid > self.amount:
            raise UserError(_('The amount prepaid can not more than contract amount.'))

    @api.constrains('line_ids')
    def check_qty(self):
        for line in self.line_ids:
            if not line.quantity or line.quantity < 0: raise UserError(_('The number is error.'))

    def check_contract_line_ids(self, vals, type):
        if 'line_ids' in vals:
            if type == 'write':
                if not vals['line_ids'][0][2] and vals['line_ids'][0][0] == 2:
                    raise UserError(_('Please add some contract details.'))
        else:
            if type == 'create':
                raise UserError(_('Please add some contract details.'))

    def write(self, vals):
        self.check_contract_line_ids(vals, 'write')
        return super(SaleContract, self).write(vals)


class SaleContractLine(models.Model):
    _name = 'ps.sale.contract.line'
    _description = 'sale contract.line'
    _rec_name = "product_id"

    product_id = fields.Many2one('product.product', string='Product')
    contract_id = fields.Many2one('ps.sale.contract', string='Contract')
    description = fields.Char(string='Description', default='Product Description')
    quantity = fields.Float(string='Quantity')
    qty_ordered = fields.Float(string='Qty Ordered', compute='_compute_qty')
    qty_delivered = fields.Float(string='Qty Delivered', compute='_compute_qty')
    qty_invoiced = fields.Float(string='Qty Invoiced', compute='_compute_qty')
    uom_id = fields.Many2one('uom.uom', string='Uom', related='product_id.uom_id')
    price = fields.Float(string='Price')
    tax_id = fields.Many2one('account.tax', string='Tax')
    amount_tax = fields.Float(string='Amount Tax', compute='_compute_amount')
    subtotal = fields.Float(string='Subtotal', compute='_compute_amount')
    state = fields.Selection([('draft', "Draft"),
                              ('confirmed', "Confirmed"),
                              ('approved', "Approved"),
                              ('closed', "Closed"),
                              ('cancelled', "Cancelled")], string='Status', related='contract_id.state',
                             default='draft', index=True, track_visibility='onchange')
    sale_order_line_ids = fields.Many2many('sale.order.line', string='Sale Order Line')
    stock_move_ids = fields.Many2many('stock.move', string='Stock Move')
    invoice_address_id = fields.Many2one('res.partner', related="contract_id.invoice_address_id",
                                         string='Invoice Address')
    product_no_variant_attribute_value_ids = fields.Many2many('product.template.attribute.value',
                                                              string='Product attribute values that do not create variants')

    @api.one
    @api.depends('quantity', 'price', 'tax_id')
    def _compute_amount(self):
        """
        Tax amount, subtotal
        """
        for line in self:
            if line.quantity and line.price and line.tax_id:
                taxes = line.tax_id.compute_all(line.price,
                                                quantity=line.quantity,
                                                product=line.product_id,
                                                partner=line.invoice_address_id)
                line.amount_tax = sum([t.get('amount', 0.0) for t in taxes.get('taxes')])
                line.subtotal = taxes['total_excluded']
            elif not line.tax_id:
                line.subtotal = line.quantity * line.price

    def unlink(self):
        for self in self:
            if self.state != 'draft':
                raise UserError("Only draft contract can delete, you should set to draft first")
        return super(SaleContractLine, self).unlink()

    def _compute_qty(self):
        '''
        quantities of ordered, deliveried and invoiced
        '''
        for self in self:
            sale_order_line = self.env['sale.order.line'].search(
                [('contract_id', '=', self.contract_id.id), ('contract_line_id', '=', self.id)])
            order_qty = 0
            qty_delivered = 0
            qty_invoiced = 0
            for line in sale_order_line:
                order_qty += line.product_uom_qty
                qty_delivered += line.qty_delivered
                qty_invoiced += line.qty_invoiced
            self.qty_ordered = order_qty
            self.qty_delivered = qty_delivered
            self.qty_invoiced = qty_invoiced

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        description = self.product_id.name
        if self.product_id.description_sale:
            description += '\n' + self.product_id.description_sale
        self.description = description
        self.tax_id = self.product_id.product_tmpl_id.taxes_id

        vals = {}
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.uom_id or (self.product_id.uom_id.id != self.uom_id.id):
            vals['uom_id'] = self.product_id.uom_id
            vals['quantity'] = self.quantity or 1.0

        product = self.product_id.with_context(
            lang=self.contract_id.customer_id.lang,
            partner=self.contract_id.customer_id,
            quantity=vals.get('product_uom_qty') or self.quantity,
            date=self.contract_id.date_confirmed,
            pricelist=self.contract_id.pricelist_id.id,
            uom=self.uom_id.id
        )

        if self.contract_id.pricelist_id and self.contract_id.customer_id:
            vals['price'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_id, self.contract_id.company_id)
        self.update(vals)
        result = {'domain': domain}
        return result

    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        # awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
        # to be able to compute the full price

        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                ptav.price_extra and
                ptav not in product.product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            product = product.with_context(
                no_variant_attributes_price_extra=no_variant_attributes_price_extra
            )

        if self.contract_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.contract_id.pricelist_id.id).price
        product_context = dict(self.env.context, partner_id=self.contract_id.customer_id.id,
                               date=self.contract_id.date_confirmed,
                               uom=self.uom_id.id)

        final_price, rule_id = self.contract_id.pricelist_id.with_context(product_context).get_product_price_rule(
            self.product_id, self.quantity or 1.0, self.contract_id.customer_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                           self.quantity,
                                                                                           self.uom_id,
                                                                                           self.contract_id.pricelist_id.id)
        if currency != self.contract_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.contract_id.pricelist_id.currency_id,
                self.contract_id.company_id, self.contract_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)
