# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PsAccountTradeRelate(models.Model):
    _name = "ps.account.trade.relate"

    trade_relate_number = fields.Char(string='Trade Relate Number')
    name = fields.Char(string='Trade Name')
    src_account_id = fields.Many2one('account.account', string='Src Account Id')
    src_direction = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], string='Src Direction')
    des_account_id = fields.Many2one('account.account', 'Des Account Id')
    des_direction = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], string='Des Direction')
    state = fields.Boolean(string='State', default=True)
