# -*- coding: utf-8 -*-

from odoo import models, fields, api ,datetime

class qingjiadan(models.Model):
    _name = 'qingjia.qingjiadan'

    name = fields.Many2one('res.users',string='申请人',required=True)
    days = fields.Integer(compute="c_days",store=True,string='天数',readonly=True)
    stardate = fields.Date(string='开始时间')
    enddate = fields.Date(string='结束时间')
    reason = fields.Text(string='请假事由')
    
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
    @api.depends('stardate','enddate')
    def c_days(self):
        self.days = (datetime.date(self.enddate)-datetime.date(self.stardate)).days