# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ps_card_ids = fields.One2many('ps.member.card', 'partner_id', string='membership card')#会员卡
    store_id = fields.Many2one('pos.config', string='Card writing store')#开卡门店
    partner_ids = fields.One2many('ps.member.card.manage.wizard', 'partner_id', string='client')  # 客户

    @api.model
    def write_card_info(self, partner_id):
        res = self.search([('id', '=', partner_id)])
        if res.ps_member_no:
            return False
        return True

    @api.model
    def search_member(self, card_no):
        res = self.search([('ps_member_no', '=', card_no)])
        if not res:
            return False
        return res.id

