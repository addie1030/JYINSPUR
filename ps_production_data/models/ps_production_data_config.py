# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError,Warning
from odoo.tools import ormcache

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ps_bom_needs_approval = fields.Boolean(string="BOM needs approval", config_parameter='ps_production_data.ps_bom_needs_approval', readonly=False)  # BOM需要审批
    ps_loss_rate_usage = fields.Selection([
        ('1', '1/(1-Attrition rate)'), # 1/(1-损耗率)
        ('2', "1*(1+Attrition rate)")], # 1*(1+损耗率)
        string="Loss rate usage", #损耗率使用方法
        config_parameter='ps_production_data.ps_loss_rate_usage',
        required=True, default='1', readonly=False)
    ps_scrap_rate_usage = fields.Selection([
        ('1', '1/(1-Rejection rate)'),  # 1/(1-废品率)
        ('2', "1*(1+Rejection rate)")],  # 1*(1+废品率)
        string="Scrap rate usage",  # 废品率使用方法
        config_parameter='ps_production_data.ps_scrap_rate_usage',
        required=True, default='1', readonly=False)

    @api.onchange('ps_bom_needs_approval')
    def _onchange_ps_bom_needs_approval(self):
        res = self.env['mrp.bom'].search([])
        if res:
            for line in res:
                line.write({"ps_bom_needs_approval": self.ps_bom_needs_approval})