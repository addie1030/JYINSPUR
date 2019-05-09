# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


# 收付款用途字典
class PaymentUse(models.Model):
    _name = "payment.use"
    _description = "Payment Use"

    business_type = fields.Selection([('sale', "Sale"), ('purchase', "Purchase"), ('transfer', 'Transfer')], translate=True)
    payment_category = fields.Selection([('receive', 'Receive'), ('payment', 'Payment'), ('transfer', "Transfer")], translate=True)
    name = fields.Char(string="name", help="Payment Use Name", translate=True)
    description = fields.Char(string="description", translate=True)
    is_send_payment = fields.Boolean(string='Payment Use Contrast', default=False)
    contrast_payment_use = fields.Many2one('payment.use', string='Payment Use')

    @api.constrains('payment_category')
    def _check_payment_category(self):
        if self.business_type in ('sale', 'purchase'):
            if self.payment_category == 'transfer':
                raise ValidationError(_("You can only choose 'payment type', please choose again!"))
        if self.business_type in ('transfer'):
            if self.payment_category != 'transfer':
                raise ValidationError(_("You can only choose 'internal transfer type', please choose again!"))


# 收付款模型增加收付款用途字段
class AddPaymentUse(models.Model):
    _inherit = "account.payment"
    payment_use = fields.Many2one("payment.use", string="Payment Use", help="Payment Use")

    @api.onchange('payment_use')
    def _onchange_payment_use(self):
        if self.payment_use.payment_category == 'receive':
            self.payment_type = 'inbound'
        elif self.payment_use.payment_category == 'payment':
            self.payment_type = 'outbound'
        elif self.payment_use.payment_category == 'transfer':
            self.payment_type = 'transfer'


    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        journal_types.update(['bank', 'cash'])
        res['domain']['journal_id'] = jrnl_filters['domain'] + [('type', 'in', list(journal_types))]
        return res
