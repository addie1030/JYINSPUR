# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ResCompany(models.Model):
    _inherit = "res.company"

    ps_bank_id = fields.Many2one('res.bank', string='Bank id', required=True)  # 开户银行名称
    ps_bank_account = fields.Char(string='Bank account', required=True)  # 开户银行账号
    ps_tax_version = fields.Selection([('1', "Aisino"), ('2', "Baiwang")],
                                     string="Corporate tax version",
                                     default='1', required=True)  # 企业税盘版本 /1：航信（白盘） /2：百旺（黑盘）
    ps_tax_disk_number = fields.Char(string='Corporate tax disk number', required=True)  # 企业税盘盘号
    ps_maximum_amount = fields.Char(string='Maximum amount of invoices(unit:  in ten thousand yuan)', required=True)  # 企业开具发票最大金额(单位：万元）
    ps_is_electronic_invoice = fields.Boolean(string="Is electronic invoices", default=False)  # 是否启用电子发票
    ps_is_information_push = fields.Boolean(string="Is information push", default=False)  # 是否启用开票信息推送
    ps_is_email = fields.Boolean(string="Is Email", default=False)  # 是否发送邮箱
    ps_is_sms = fields.Boolean(string="Is SMS", default=False)  # 是否手机短信通知

