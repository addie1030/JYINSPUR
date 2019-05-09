# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleSubscriptionWizard(models.TransientModel):
    _name = 'sale.subscription.wizard'
    _description = 'Subscription Upsell wizard'

    def _default_subscription(self):
        return self.env['sale.subscription'].browse(self._context.get('active_id'))

    subscription_id = fields.Many2one('sale.subscription', string="Subscription", required=True, default=_default_subscription, ondelete="cascade")
    option_lines = fields.One2many('sale.subscription.wizard.option', 'wizard_id', string="Options")
    date_from = fields.Date('Discount Date', default=fields.Date.today,
                            help="The discount applied when creating a sales order will be computed as the ratio between "
                                 "the full invoicing period of the subscription and the period between this date and the "
                                 "next invoicing date.")

    @api.multi
    def create_sale_order(self):
        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(self.subscription_id.partner_id.id)
        sale_order_obj = self.env['sale.order']
        team = self.env['crm.team']._get_default_team_id(user_id=self.subscription_id.user_id.id)
        new_order_vals = {
            'partner_id': self.subscription_id.partner_id.id,
            'analytic_account_id': self.subscription_id.analytic_account_id.id,
            'team_id': team and team.id,
            'pricelist_id': self.subscription_id.pricelist_id.id,
            'fiscal_position_id': fpos_id,
            'subscription_management': 'upsell',
            'origin': self.subscription_id.code,
        }
        # we don't override the default if no payment terms has been set on the customer
        if self.subscription_id.partner_id.property_payment_term_id:
            new_order_vals['payment_term_id'] = self.subscription_id.partner_id.property_payment_term_id.id
        order = sale_order_obj.create(new_order_vals)
        for line in self.option_lines:
            self.subscription_id.partial_invoice_line(order, line, date_from=self.date_from)
        order.order_line._compute_tax_id()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": order.id,
        }

    def _prepare_subscription_lines(self):
        rec_lines = []
        for line in self.option_lines:
            rec_line = False
            for account_line in self.subscription_id.recurring_invoice_line_ids:
                if (line.product_id, line.uom_id) == (account_line.product_id, account_line.uom_id):
                    rec_line = (1, account_line.id, {'quantity': account_line.quantity + line.quantity})
            if not rec_line:
                rec_line = (0, 0, {'product_id': line.product_id.id,
                                   'name': line.name,
                                   'quantity': line.quantity,
                                   'uom_id': line.uom_id.id,
                                   'price_unit': self.subscription_id.pricelist_id.with_context({'uom': line.uom_id.id}).get_product_price(line.product_id, 1, False)
                                   })
            rec_lines.append(rec_line)
        return rec_lines

    @api.multi
    def add_lines(self):
        for wiz in self:
            rec_lines = wiz._prepare_subscription_lines()
            wiz.subscription_id.sudo().write({'recurring_invoice_line_ids': rec_lines})
        return True


class SaleSubscriptionWizardOption(models.TransientModel):
    _name = "sale.subscription.wizard.option"
    _description = 'Subscription Upsell Lines Wizard'

    name = fields.Char(string="Description")
    wizard_id = fields.Many2one('sale.subscription.wizard', required=True, ondelete="cascade")
    product_id = fields.Many2one('product.product', required=True, domain="[('recurring_invoice', '=', True)]", ondelete="cascade")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True, ondelete="cascade")
    quantity = fields.Float(default=1.0)

    @api.onchange("product_id")
    def onchange_product_id(self):
        domain = {}
        if not self.product_id:
            domain['uom_id'] = []
        else:
            self.name = self.product_id.get_product_multiline_description_sale()

            if not self.uom_id:
                self.uom_id = self.product_id.uom_id.id
            domain['uom_id'] = [('category_id', '=', self.product_id.uom_id.category_id.id)]

        return {'domain': domain}
