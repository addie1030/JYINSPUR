# -*- coding: utf-8 -*-
import time
import math

from datetime import datetime
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools


############################################
# describe：1、固定资产用途
#           2、固定资产状态
#           3、固定资产减少原因
#           4、主要附属设备
# create date: 20180813
# update date: 20180815
# author：Rec Cao
############################################

class PsAccountAssetsUse(models.Model):
    _name = 'account.assets.use'
    _description = '固定资产用途字典'

    code = fields.Char(string="用途编号", required=True)
    name = fields.Char(string="用途名称", required=True)
    ps_assets_isstorage = fields.Boolean(string="是否封存")
    # SQL约束
    _sql_constraints = [('code_unique', 'UNIQUE(code)', "Code repetition ！"),
                        ('name_unique', 'UNIQUE(name)', "Name repetition ！")]


class PsAccountAssetsStatus(models.Model):
    _name = 'account.assets.status'
    _description = '固定资产状态字典'

    code = fields.Char(string="状态编号", required=True)
    name = fields.Char(string="状态名称", required=True)
    ps_assets_depreciate = fields.Boolean(string="折旧计提")
    ps_assets_isstorage = fields.Boolean(string="是否封存")
    # SQL约束
    _sql_constraints = [('code_unique', 'UNIQUE(code)', "Code repetition ！"),
                        ('name_unique', 'UNIQUE(name)', "Name repetition ！")]


class PsAccountAssetsReduceFor(models.Model):
    _name = 'account.assets.reducefor'
    _description = '固定资产减少原因'

    code = fields.Char(string="去向编号", required=True)
    name = fields.Char(string="去向名称", required=True)
    # SQL约束
    _sql_constraints = [('code_unique', 'UNIQUE(code)', "Code repetition ！"),
                        ('name_unique', 'UNIQUE(name)', "Name repetition ！")]


class PsAccountAssetsAccessoryLsttb(models.Model):
    _name = 'account.assets.accessory.lsttb'
    _description = '附属设备明细表'

    code = fields.Char(string="部件编号")
    name = fields.Char(string="部件名称")
    accessory_spec = fields.Char(string="规格型号")
    accessory_uom = fields.Char(string="计量单位")
    accessory_num = fields.Float(digits=(16, 2), string="数量")
    accessory_price = fields.Float(digits=(16, 2), string="价值")
    accessory_manufacturer = fields.Char(string="生产厂家")
    accessory_d_id = fields.Many2one("account.assets.accessory.prmytb", string="主记录编号")

    # @api.constrains('accessory_d_id')
    # def _check_code_is_exist(self):
    #     print(self.accessory_d_id.id)
    #     recs = self.search(
    #         [('accessory_d_id', '=', self.accessory_d_id.id)])
    #     code = []
    #     if recs:
    #         for r in recs:
    #             code.append(r.code)
    #         print("code:", code)
    #     code2 = []
    #     for i in self:
    #         code2.append(i.code)
    #     print("code2", code2)
    #
    #     code_set = set(code)
    #     print(code_set)
    #     for i_code in code_set:
    #         count = 0
    #         for j_code in code:
    #             if i_code == j_code:
    #                 count += 1
    #         print(i_code, ":", count)
    #         # if self.code in code:
    #         #     raise ValidationError('已经存在部件编号【' + self.code + '】，请重新输入.')


class PsAccountAssetsAccessoryPrmytb(models.Model):
    _name = 'account.assets.accessory.prmytb'
    _description = '资产附属设备主表'

    name = fields.Char(string="资产名称")
    assets_id = fields.Many2one("ps.account.asset", string="资产编号")
    accessory_m_ids = fields.One2many("account.assets.accessory.lsttb", 'accessory_d_id', string="备注")
    # SQL约束
    _sql_constraints = [('name_unique', 'UNIQUE(name)', "已存在此资产编号相关明细!")]

    @api.onchange('assets_id')
    def _set_name_value(self):
        self.ensure_one()
        if self.assets_id:
            self.name = self.assets_id.name


