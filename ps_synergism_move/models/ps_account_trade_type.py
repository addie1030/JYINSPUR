# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PsAccountTradeType(models.Model):
    _name = "ps.account.trade.type"

    trade_type_number = fields.Char(string='Trade Type Number')
    name = fields.Char(string='Type Name')
