# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'

    ps_asset_uom_id = fields.Many2one('uom.uom', string='Default UOM') #默认计量单位
    ps_asset_state_id = fields.Many2one('ps.asset.state', string='Default Asset State') #默认资产状态
    ps_account_asset_disposal_id = fields.Many2one('account.account', string='Asset disposal account') #资产清理科目
    ps_net_salvage_rate = fields.Integer(string='Default Net Salvage Rate', default=3) #默认净残值率
    account_depreciation_id = fields.Many2one(string='Depreciation Entries: Depreciation Account') #字段继承修改string：折旧分录：折旧科目



