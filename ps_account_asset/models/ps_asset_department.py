# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PsAssetDepartment(models.Model):
    _name = 'ps.asset.department'

    ps_proportional = fields.Integer(string='Distribution Proportional', requird=True) #分配比例
    ps_asset_id = fields.Many2one('account.asset.asset', string='Asset') #资产
    ps_analytic_id = fields.Many2one('account.analytic.account', string='Analysis Account', required=True) #分析账户



