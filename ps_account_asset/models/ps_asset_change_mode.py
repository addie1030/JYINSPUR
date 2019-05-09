# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PsAssetChangeMode(models.Model):
    _name = 'ps.asset.change.mode'
    _description = 'Asset Change Mode'

    name = fields.Char(string='Name', requird=True)     #变动方式名称
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)   #公司
    category = fields.Selection([('add','Add'),('reduce','Reduce')],string='Category')    #类别
    is_default = fields.Boolean(string='Default', default=False)  #是否默认
    active = fields.Boolean(default=True)   #是否有效
    account_change_id = fields.Many2one('account.account', string='Change Account',
                                        domain=[('internal_type','=','other'), ('deprecated', '=', False)])     #变动分录-资产科目
    journal_id = fields.Many2one('account.journal', string='Journal')    #账簿类型


    @api.constrains('is_default')
    def _check_default(self):
        for r in self:
            if r.is_default:
                recs = self.search([('id', '!=', r.id),('category','=',r.category)])
                if recs:
                    recs.write({'is_default': False})