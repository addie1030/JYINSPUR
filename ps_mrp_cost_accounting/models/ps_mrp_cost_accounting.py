# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PsMrpCostAccounting(models.Model):
    _name = 'ps.mrp.cost.accounting'

    # code = fields.Char(string='Number')
    name = fields.Char(string='Name')
    name_id = fields.Many2one('account.analytic.account', string='Analytic Name')
    workcenter_id = fields.Many2many('mrp.workcenter', string='WorkCenter')
    related_object = fields.Selection([('workcenter', 'workcenter')], string='Related Object')
    # 前端暂时不显示
    department_id = fields.Many2one('hr.department', string='Department')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    WIPcompute_id = fields.Many2one('ps.mrp.expenses.standard', string='WIPcompute',
                                    domain=[('standard_type', '=', 'wipstandard')])

    # @api.onchange('related_object')
    # def _onchange_department_id_company_id(self):
    #     if self.related_object in ['workcenter']:
    #         self.department_id = None
    #     elif self.related_object in ['department']:
    #         self.workcenter_id = None
    #
    # @api.constrains('related_object')
    # def _check_ids(self):
    #     for rec in self:
    #         if rec.related_object in ['workcenter']:
    #             rec.department_id = None
    #         elif rec.related_object in ['department']:
    #             rec.workcenter_id = None
