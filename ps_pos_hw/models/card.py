# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class PsMemberCard(models.Model):
    _name = 'ps.member.card'
    _description = _('membership card')

    @api.model
    def _default_card_no(self, partner_id):
        partner_id = self.env['res.partner'].sudo().browse(partner_id)
        seq = self.env['ir.sequence'].sudo().next_by_code('ps.member.card')
        db = str(self.env.cr.dbname)[:4] # TODO 参数
        db = db + (4-len(db)) * '0'
        db = ''.join([hex(ord(db[i]))[2:] for i in range(len(db))])
        store = hex(partner_id.store_id.id)[2:][:4].zfill(4)
        return '{db}{store}{seq}'.format(db=db, store=store, seq=seq)

    @api.model
    def _default_name(self, partner_id):
        count = self.search_count([('partner_id', '=', partner_id)]) + 1
        return str(count).zfill(4)

    name = fields.Char(string='Index', index=True)#序号
    card_serial = fields.Char(string='Serial No', index=True)#序列号
    state = fields.Selection([
        ('normal', 'normal'),#正常
        ('lost', 'lost')#挂失
    ], string='status', index=True, default='normal')#状态
    partner_id = fields.Many2one('res.partner', string='client')#客户
    card_no = fields.Char(string='Member Card No', index=True, size=32)#会员卡号
    create_date = fields.Datetime(string='Creation date')#创建日期
    write_date = fields.Datetime(string='Updated date')#更新日期

    @api.model
    def create(self, vals):
        if (not vals.get('name', None)) and vals.get('partner_id', None):
            vals['name'] = self._default_name(vals.get('partner_id', None))
        return super(PsMemberCard, self).create(vals)


    @api.multi
    def card_lost(self):
        self.ensure_one()
        self.write({'state': 'lost'})
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
        self.write({'state': 'normal'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ps.member.card.manage.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'active_id': self.partner_id.id, 'active_model': 'res.partner', 'partner_id': self.partner_id.id},
        }

    @api.model
    def write_card_info_ex(self, card_serial, card_no, state, partner_id):
        self.create({
            'card_serial': card_serial,
            'state': state,
            'card_no': card_no,
        })
        res = self.env['res.partner'].sudo().search([('id', '=', partner_id)])
        res.ps_member_no = card_no
        return True, partner_id, card_no

