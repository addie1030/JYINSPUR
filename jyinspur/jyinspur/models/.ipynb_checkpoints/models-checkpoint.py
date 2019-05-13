# -*- coding: utf-8 -*-

from odoo import models, fields, api

class soft(models.Model):
    _name = 'jyinspur.soft'

    name = fields.Char('名称')
    ggxh = fields.Char('规格型号')
    price = fields.Float('价格')
    soft_type = fields.Selection([('single','单组织'),('multiple','多组织')],'类型')
    #price = fields.Float(compute="_value_pc", store=True)
    description = fields.Text('描述')
    jldw = fields.Many2one('uom.uom',string='单位')
    #qm = fields.Char(string='全名',compute='qm_compute')#compute为调用函数名
    state = fields.Selection([('draft','草稿'),('processing','审批中'),('done','已审批')],readonly = True,string='状态',default='draft')
    
    
   # @api.depends('name','ggxh')  #填入需要的参数
   # def qm_compute(self):
       # self.qm = str(self.name) + '-' + str(self.ggxh)  #需要加上str()函数不然提示数据类型错误

    #@api.depends('value')
    #def _value_pc(self):
        #self.value2 = float(self.value) / 100
    
    @api.multi
    def button_draft(self):
        self.write({'state': 'draft'})
        return {}
    
    @api.multi
    def button_done(self):
        self.write({'state': 'done'})
        return {}
    
    @api.multi
    def button_processing(self):
        self.write({'state': 'processing'})
        return {}