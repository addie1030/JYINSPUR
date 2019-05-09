# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class PsMemberCardReadWiard(models.TransientModel):
    _name = 'ps.member.card.read.wizard'

    card_serial = fields.Char(string='Serial No', index=True)#序列号
    card_id = fields.Many2one('ps.member.card', string=_('membership card'))#会员卡
    name = fields.Char(string='Index', related='card_id.name')#序号
    state = fields.Selection(string='status', related='card_id.state')#状态
    partner_id = fields.Many2one('res.partner', string='client', related='card_id.partner_id')#客户
    card_no = fields.Char(string='Member No', related='card_id.card_no')#会员号
    card_create_date = fields.Datetime(string='Creation date', related='card_id.create_date')#创建日期
    card_write_date = fields.Datetime(string='Updated date', related='card_id.write_date')#更新日期

    @api.model
    def default_get(self, fields):
        res = super(PsMemberCardReadWiard, self).default_get(fields)
        card_id = card_serial = card_no = None
        if self.env.context.get('active_id', None) and self.env.context.get('active_model', None) == 'ps.member.card':
            card_id = self.env.context.get('active_id')
            card_obj = self.env['ps.member.card'].browse(card_id)
            res['card_id'] = card_id
            res['card_serial'] = card_serial
            res['card_no'] = card_no
        elif self.env.context.get('card_serial', None) and self.env.context.get('card_no', None):
            card_id = self.env['ps.member.card'].search([
                ('card_serial', '=',  self.env.context.get('card_serial', None)),
                ('card_no', '=',  self.env.context.get('card_no', None))
            ])
            if card_id:
                card_id = card_id[0]
                res['card_id'] = card_id.id
            res['card_serial'] = self.env.context.get('card_serial', None)
            res['card_no'] = self.env.context.get('card_no', None)
        return res

    @api.multi
    def confirm(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def card_lost(self):
        self.ensure_one()
        self.card_id.write({'state': 'lost'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ps.member.card.manage.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'active_id': self.partner_id.id, 'active_model': 'res.partner', 'partner_id': self.partner_id.id},
        }

    @api.multi
    def card_normal(self):
        self.ensure_one()
        self.card_id.write({'state': 'normal'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ps.member.card.manage.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'active_id': self.partner_id.id, 'active_model': 'res.partner', 'partner_id': self.partner_id.id},
        }

