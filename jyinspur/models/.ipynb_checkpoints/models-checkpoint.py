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
    qm = fields.Char(string='全名',compute='qm_compute')
    
    
    @api.depends('name','ggxh')
    def qm_compute(self):
        self.qm = str(self.name) + '-' + str(self.ggxh)

    #@api.depends('value')
    #def _value_pc(self):
        #self.value2 = float(self.value) / 100