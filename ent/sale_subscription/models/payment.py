# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PaymentToken(models.Model):
    _name = 'payment.token'
    _inherit = 'payment.token'

    @api.multi
    def get_linked_records(self):
        res = super(PaymentToken, self).get_linked_records()

        for token in self:
            subscriptions = self.env['sale.subscription'].search([('payment_token_id', '=', token.id)])
            for sub in subscriptions:
                res[token.id].append({
                    'description': subscriptions._description,
                    'id': sub.id,
                    'name': sub.name,
                    'url': '/my/subscription/' + str(sub.id) + '/' + str(sub.uuid)})

        return res
