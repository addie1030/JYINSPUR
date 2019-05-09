# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


# 卸载合并报表之后清除系统参数
class module(models.Model):
    _inherit = 'ir.module.module'

    @api.multi
    def module_uninstall(self):
        for module_to_remove in self:
            if module_to_remove.name == "ps_combined_statements":
                self.env['ir.config_parameter'].search([('key','=','combined.statements.decimal')]).unlink()
        return super(module, self).module_uninstall()