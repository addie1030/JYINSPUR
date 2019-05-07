# -*- coding: utf-8 -*-

from odoo import models, fields, api

class qingjiadan(models.Model):
    _name = 'qingjia.qingjiadan'

    name = fields.Char(string='申请人')
    days = fields.Integer(string='天数')
    stardate = fields.Date(string='开始时间')
    reason = fields.Text(string='请假事由')
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100