# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


# check customer in sale order
class CheckSaleOrderRule(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def check_sale_order(self):
        for customer in self:
            # search customer credit profile
            credit_file = self.env['ps.credit.profile'].search([("partner_id", '=', customer.partner_id.id),
                                                                ('date_start', '<=', fields.datetime.now()),
                                                                ('date_end', '>=', fields.datetime.now()),
                                                                ('state', '=', 'confirmed'),
                                                                ], limit=1)

            # credit_file.check_rule_id
            scheme_id = credit_file.check_scheme_id
            # check credit limit
            rule = self.env['ps.credit.check.rule'].search([('scheme_id', '=', scheme_id.id),
                                                            ('document', '=', 'sales_order')], limit=1)
            # find customer credit data
            usage = self.env['ps.credit.usage'].search([('partner_id', '=', customer.partner_id.id),
                                                        ])
            message = ''
            flag = []
            if usage and credit_file:
                check = 0
                if rule.check_credit_limit:
                    check += 1
                    if customer.amount_total > usage.balance and customer.amount_total > usage.order_limit:
                        message = message + (_(
                            "Check credit limit not pass (Order amount:%9.2f bigger than usage balance:%9.2f and Order amount:%9.2f bigger than order_limit:%9.2f)\n") % (
                                                 customer.amount_total, usage.balance, customer.amount_total,
                                                 usage.order_limit))
                        flag.append(False)
                    else:
                        if customer.amount_total > usage.balance:
                            message = message + (_(
                                "Check credit limit not pass (Order amount:%9.2f bigger than usage balance:%9.2f)\n") % (
                                                     customer.amount_total, usage.balance))
                            flag.append(False)
                        if customer.amount_total > usage.order_limit:
                            message = message + (_(
                                "Check credit limit not pass (Order amount:%9.2f bigger than order_limit:%9.2f)\n") % (
                                                     customer.amount_total, usage.order_limit))
                            flag.append(False)
                if rule.check_credit_ratio:
                    check += 1
                    if customer.amount_total > (usage.credit_limit + usage.credit_ratio_limit - usage.used_limit):
                        message = message + (
                            _(
                                "Check credit ratio not pass (Order amount:%9.2f bigger than credit ratio limit:%9.2f)\n") % (
                                customer.amount_total,
                                usage.credit_limit + usage.credit_ratio_limit - usage.used_limit))
                        flag.append(False)
                if rule.check_overdue_days:
                    check += 1
                    if usage.actual_overdue_days > usage.overdue_days:
                        message = message + (_(
                            "Check overdue days not pass (Actual overdue days:%9.2f bigger than overdue:%9.2f)\n") % (
                                                 usage.actual_overdue_days, usage.overdue_days))
                        flag.append(False)
                if rule.check_overdue_amount:
                    check += 1
                    if usage.overdue_limit < usage.actual_overdue_limit:
                        message = message + (_(
                            "Check overdue amount not pass (Actual overdue:%9.2f bigger then limit:%9.2f)\n") % (
                                                 usage.actual_overdue_limit, usage.overdue_limit))
                        flag.append(False)
                if rule.check_overdue_ratio:
                    check += 1
                    if usage.overdue_ratio < usage.actual_overdue_ratio:
                        message = message + (_(
                            "Check overdue ratio not pass (Actual overdue ratio:%9.2f bigger than overdue ratio:%9.2f)\n") % (
                                                 usage.actual_overdue_ratio, usage.overdue_ratio))
                        flag.append(False)
                if rule.excessive_condition == 'multi':
                    if len(flag) < check:
                        message = ''
            return message

    def action_confirm(self):
        msg = self.check_sale_order()
        continue_sale = self.env.context.get('continue_sale', False)
        if msg:
            if continue_sale:
                super(CheckSaleOrderRule, self).action_confirm()
            else:
                return self.call_confirm_wizard(msg)
        else:
            super(CheckSaleOrderRule, self).action_confirm()

    @api.multi
    def call_confirm_wizard(self, msg):
        usage = self.env['ps.credit.usage'].search([('partner_id', '=', self.partner_id.id)])
        wizard_form = self.env.ref('ps_credit_management.ps_credit_confirm_wizard', False)
        view_id = self.env['ps.credit.confirm.wizard']
        vals = {
            'name': 'sales order check wizard',
            'customer_id': self.partner_id.id,
            'amount_total': self.amount_total,
            'balance': usage.balance,
            'order': self.id,
            'message': msg,

        }
        new = view_id.create(vals)
        return {
            'name': _('Credit Check Warning'),
            'type': 'ir.actions.act_window',
            'res_model': 'ps.credit.confirm.wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def write(self, vals):
        # find customer credit data

        if ('product_uom_qty' in vals and vals['product_uom_qty'] > self.product_uom_qty) or (
                        'price_unit' in vals and vals[
                    'price_unit'] > self.price_unit) and self.order_id.state == "sale":
            msg = self.order_id.check_sale_order()
            if msg:
                if not self.user_has_groups('sales_team.group_sale_manager'):
                    raise UserError(_(msg))
                else:
                    self.order_id.message_post(body=msg)
                    return super(SaleOrderLine, self).write(vals)

        return super(SaleOrderLine, self).write(vals)


# find stock rule
class CheckStockRule(models.Model):
    _inherit = "stock.picking"

    def _get_product_price(self, product_id):
        picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')])
        picking_id = self.env["stock.picking"].search(
            [("picking_type_id", "in", picking_type_id.ids), ("sale_id", "=", self.sale_id.id),
             ("state", "not in", ['cancel', 'done'])])

        move_id = self.env["stock.move"].search(
            [("picking_id", "=", picking_id.id), ("product_id", "=", product_id.id)],
            limit=1)
        return move_id.ps_order_price

    @api.multi
    def check_stock_picking(self, type=None):
        rule = ''
        for customer in self:
            credit_file = self.env['ps.credit.profile'].search([("partner_id", '=', customer.partner_id.id),
                                                                ('date_start', '<=', fields.datetime.now()),
                                                                ('date_end', '>=', fields.datetime.now()),
                                                                ('state', '=', 'confirmed')], limit=1)
            # credit_file.check_rule_id
            scheme_id = credit_file.check_scheme_id
            # check credit limit
            stock_msg = ''
            sum = 0
            if type == "Pick":
                rule = self.env['ps.credit.check.rule'].search([('scheme_id', '=', scheme_id.id),
                                                                ('document', '=', 'stock_picking')], limit=1)
                # find price
                if self.sale_id:

                    stock_move_obj = self.env["stock.move"].search([("picking_id", "=", self.id)])
                    # find num

                    for stock_move in stock_move_obj:
                        stock_move.ps_order_price = self._get_product_price(stock_move.product_id)
                        if stock_move.quantity_done > 0:
                            price = stock_move.ps_order_price * stock_move.quantity_done
                            product = stock_move.product_id.name
                            stock_msg = stock_msg + (_("Product name: %s, price: %6.2f,qty: %6.2f\n") % (
                                product, stock_move.ps_order_price, stock_move.quantity_done))
                        else:
                            price = stock_move.ps_order_price * stock_move.product_uom_qty
                            product = stock_move.product_id.name
                            stock_msg = stock_msg + (
                                _("Product name: %s, price: %6.2f,qty: %6.2f\n") % (
                                    product, stock_move.ps_order_price, stock_move.product_uom_qty))
                        sum += price
                else:

                    stock_move_obj = self.env["stock.move"].search([("picking_id", "=", self.id)])
                    # find num
                    for stock_move in stock_move_obj:
                        if stock_move.quantity_done > 0:
                            price = stock_move.ps_stock_price * stock_move.quantity_done
                            product = stock_move.product_id.name
                            stock_msg = stock_msg + (
                                _("Product name: %s, price: %6.2f,qty: %6.2f\n") % (
                                    product, stock_move.ps_stock_price, stock_move.quantity_done))
                        else:
                            price = stock_move.ps_stock_price * stock_move.product_uom_qty
                            product = stock_move.product_id.name
                            stock_msg = stock_msg + (
                                _("Product name: %s, price: %6.2f,qty: %6.2f\n") % (
                                    product, stock_move.ps_stock_price, stock_move.product_uom_qty))
                        sum += price

            elif type == 'outgoing':
                rule = self.env['ps.credit.check.rule'].search([('scheme_id', '=', scheme_id.id),
                                                                ('document', '=', 'stock_out')], limit=1)
                # find price
                if self.sale_id:
                    stock_move_obj = self.env["stock.move"].search([("picking_id", "=", self.id)])
                    # find num

                    for stock_move in stock_move_obj:
                        if stock_move.quantity_done > 0:
                            price = stock_move.ps_order_price * stock_move.quantity_done
                            product = stock_move.product_id.name
                            stock_msg = stock_msg + (
                                _("Product name: %s, price: %6.2f,qty: %6.2f\n") % (
                                    product, stock_move.ps_order_price, stock_move.quantity_done))
                        else:
                            price = stock_move.ps_order_price * stock_move.product_uom_qty
                            product = stock_move.product_id.name
                            stock_msg = stock_msg + (
                                _("Product name: %s, price: %6.2f,qty: %6.2f\n") % (
                                    product, stock_move.ps_order_price, stock_move.product_uom_qty))
                        sum += price
                else:

                    stock_move_obj = self.env["stock.move"].search([("picking_id", "=", self.id)])
                    # find num

                    for stock_move in stock_move_obj:
                        if stock_move.quantity_done > 0:
                            price = stock_move.ps_stock_price * stock_move.quantity_done
                            product = stock_move.product_id.name
                            stock_msg = stock_msg + (
                                _("Product name: %s, price: %6.2f,qty: %6.2f\n") % (
                                    product, stock_move.ps_stock_price, stock_move.quantity_done))
                        else:
                            price = stock_move.ps_stock_price * stock_move.product_uom_qty
                            product = stock_move.product_id.name
                            stock_msg = stock_msg + (
                                _("Product name: %s, price: %6.2f,qty: %6.2f\n") % (
                                    product, stock_move.ps_stock_price, stock_move.product_uom_qty))
                        sum += price

            # search customer data
            usage = self.env['ps.credit.usage'].search([('partner_id', '=', customer.partner_id.id),
                                                        ])

            message = ''
            flag = []
            if usage and credit_file:
                check = 0
                order_price = self.sale_id
                res_amount = sum - order_price.amount_total
                if rule.check_credit_limit:
                    check += 1
                    if res_amount > usage.balance and res_amount > usage.order_limit:
                        message = message + (_(
                                "Check credit limit not pass (Check amount(move amount-order amount):%9.2f bigger than usage balance:%9.2f and Check amount(move amount-order amount):%9.2f bigger than order_limit:%9.2f)\n") % (
                                                 res_amount, usage.balance))
                        flag.append(False)
                    else:
                        if res_amount > usage.balance:
                            message = message + (_(
                                "Check credit limit not pass (Check amount(move amount-order amount):%9.2f bigger than usage balance:%9.2f)\n") % (
                                                     res_amount, usage.balance))
                            flag.append(False)
                        if res_amount > usage.order_limit:
                            message = message + (_(
                                "Check credit limit not pass (Check amount(move amount-order amount):%9.2f bigger than order_limit:%9.2f)\n") % (
                                                     res_amount, usage.order_limit))
                            flag.append(False)

                if rule.check_credit_ratio:
                    check += 1
                    if res_amount > (usage.credit_limit + usage.credit_ratio_limit - usage.used_limit):
                        message = message + (
                            _(
                                "Check credit ratio not pass (Check amount(move amount-order amount):%9.2f bigger than credit ratio limit:%9.2f)\n") % (
                                res_amount, usage.credit_limit + usage.credit_ratio_limit - usage.used_limit))
                        flag.append(False)
                if rule.check_overdue_days:
                    check += 1
                    if usage.actual_overdue_days > usage.overdue_days:
                        message = message + (_(
                            "Check overdue days not pass (Actual overdue days:%9.2f bigger than overdue:%9.2f)\n") % (
                                                 usage.actual_overdue_days, usage.overdue_days))
                        flag.append(False)
                if rule.check_overdue_amount:
                    check += 1
                    if usage.overdue_limit < usage.actual_overdue_limit:
                        message = message + (_(
                            "Check overdue amount not pass (Actual overdue:%9.2f bigger then limit:%9.2f)\n") % (
                                                 usage.actual_overdue_limit, usage.overdue_limit))
                        flag.append(False)
                if rule.check_overdue_ratio:
                    check += 1
                    if usage.overdue_ratio < usage.actual_overdue_ratio:
                        message = message + (_(
                            "Check overdue ratio not pass (Actual overdue ratio:%9.2f bigger than overdue ratio:%9.2f)\n") % (
                                                 usage.actual_overdue_ratio, usage.overdue_ratio))
                        flag.append(False)
                if rule.excessive_condition == 'multi':
                    if len(flag) < check:
                        message = ''
                    else:
                        message = message + stock_msg
                else:
                    if check > 0 and message:
                        message = message + stock_msg
            return message

    def button_validate(self):
        picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')])
        picking_type = self.env['stock.picking.type'].search([('name', '=', 'Pick')])
        continue_move = self.env.context.get('continue_sale', False)
        if self.picking_type_id in picking_type_id:
            message = self.check_stock_picking(type='outgoing')
            if message:
                if continue_move:
                    super(CheckStockRule, self).button_validate()
                else:
                    return self._call_stock_confirm_wizard(message)

        elif self.picking_type_id in picking_type:
            message = self.check_stock_picking(type="Pick")
            if message:
                if continue_move:
                    super(CheckStockRule, self).button_validate()
                else:
                    return self._call_stock_confirm_wizard(message)
        return super(CheckStockRule, self).button_validate()

    @api.multi
    def _call_stock_confirm_wizard(self, msg):
        usage = self.env['ps.credit.usage'].search([('partner_id', '=', self.partner_id.id)])
        wizard_form = self.env.ref('ps_credit_management.ps_credit_confirm_stock_wizard', False)
        view_id = self.env['ps.credit.confirm.stock.wizard']
        vals = {
            'name': 'stock move check wizard',
            'customer_id': self.partner_id.id,
            'amount_total': self.sale_id.amount_total,
            'balance': usage.balance,
            'pick_id': self.id,
            'message': msg,

        }
        new = view_id.create(vals)
        return {
            'name': _('Credit Check Warning'),
            'type': 'ir.actions.act_window',
            'res_model': 'ps.credit.confirm.stock.wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }
