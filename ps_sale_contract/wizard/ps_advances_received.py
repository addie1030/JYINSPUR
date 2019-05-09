# -*- coding: utf-8 -*-
import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Advances(models.TransientModel):
    _name = "ps_advances_received.wizard"
    _description = 'Wizard to add advances received'

    @api.model
    def _default_product_id(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        return self.env['product.product'].browse(int(product_id))

    customer_id = fields.Many2one("res.partner", string="Customer")
    amount = fields.Float(string="Contract Amount")
    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position')
    amount_prepaid = fields.Float(string="Amount prepaid", store=True)
    product_id = fields.Many2one('product.product', string='Down Payment Product', domain=[('type', '=', 'service')],
                                 default=_default_product_id)

    # Get context
    @api.model
    def default_get(self, fields):
        rec = super(Advances, self).default_get(fields)
        if 'customer_id' in rec:
            contract = self.env['ps.sale.contract'].browse(rec['customer_id'])
            rec['customer_id'] = contract.customer_id.id
            rec['amount'] = contract.amount
        return rec

    def _get_amount_prepaid(self):
        if self.amount_prepaid <= 0.00:
            raise UserError(_('The value of the prepaid amount must be positive.'))
        else:
            return self.amount_prepaid

    def _get_account_id(self):
        ir_property_obj = self.env['ir.property']
        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id or self.product_id.categ_id.property_account_income_categ_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = self.fiscal_position_id.map_account(inc_acc).id if inc_acc else False

        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s".'
                  'You may have to install a chart of account from Accounting app, settings menu.') %
                (self.product_id.name,))
        return account_id

    @api.multi
    def create_invoices(self):
        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        inv_obj = self.env['account.invoice']
        sale_contract = self.env['ps.sale.contract'].browse(self._context.get('active_ids', []))
        for contract in sale_contract:
            inv_obj.create({
                'partner_id': contract.customer_id.id,
                'date_invoice': time.strftime("%Y-%m-%d"),
                'origin': sale_contract.name,
                'date_due': sale_contract.valid_to,
                'invoice_line_ids': [(0, 0, {
                    'name': _('Down Payment'),
                    'account_id': self._get_account_id(),
                    'price_unit': self._get_amount_prepaid(),
                    'quantity': 1.0,
                    'discount': 0.0,
                    'product_id': self.product_id.id,
                })],
            })
