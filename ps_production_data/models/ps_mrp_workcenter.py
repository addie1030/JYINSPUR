# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    ps_salary_type = fields.Selection([
        ('time', 'reckon by time'),  # 计时
        ('piece', 'reckon by the piece')],  # 计件
        string="Salary type",  # 工资类型
        require=True, default='piece')
    ps_is_key = fields.Boolean(string="Whether it is a key work center",require=True,default=False) #是否关键
    ps_is_outsource = fields.Boolean(string="Whether it is an outsourcing unit",require=True,default=False) #是否外协
    ps_outsourcing_unit = fields.Many2one('res.partner',string="Outsourcing unit") #外协单位