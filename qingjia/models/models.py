# -*- coding: utf-8 -*-

from odoo import models, fields, api 

class qingjiadan(models.Model):
    WORKFLOW_STATE_SELECTION = [
        ('draft','草稿'),
        ('confirm','待审批'),
        ('complete','已完成')
    ]
    _name = 'qingjia.qingjiadan'

    name = fields.Many2one('res.users',string='申请人',required=True)
    days = fields.Integer(string='天数')
    stardate = fields.Date(string='开始时间')
    enddate = fields.Date(string='结束时间')
    reason = fields.Text(string='请假事由')
    state = fields.Selection(WORKFLOW_STATE_SELECTION,default='draft',string='状态',readonly=True)
    
    @api.multi
    def do_confirm(self):
        self.state='confirm'
        return True
    
    @api.multi
    def do_complete(self):
        self.state='complete'
        return True
    
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
    #@api.depends('stardate','enddate')
    #def c_days(self):
        #self.days = (self.enddate-self.stardate).days