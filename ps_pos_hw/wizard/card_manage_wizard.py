# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class PsMemberCardManageWiard(models.TransientModel):
    _name = 'ps.member.card.manage.wizard'

    partner_id = fields.Many2one('res.partner', string='client')#客户
    ps_card_ids = fields.One2many('ps.member.card', string='membership card', related='partner_id.ps_card_ids')#会员卡
    number = fields.Char(string='Member No', related='partner_id.ps_member_no')#会员号

    @api.model
    def default_get(self, fields):
        res = super(PsMemberCardManageWiard, self).default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'res.partner':
            res['partner_id'] = self.env.context.get('active_id')
        return res

    @api.multi
    def confirm(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def card_write(self):
        partner_id = self.partner_id.id
        card_no = self.env['ps.member.card']._default_card_no(partner_id)
        return {
            'type': 'ir.actions.exec_js',
            'exec': "window.posmodel.rfid_write({params: {card_no: '%s'}, context: {partner_id: %d, sync: true}});" % (card_no, partner_id)
        }

    @api.multi
    def card_read(self):
        return {
            'type': 'ir.actions.exec_js',
            'exec': "window.posmodel.rfid_read();"
        }



