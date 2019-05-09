# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ps_is_send_payment = fields.Boolean(string='Send Payment and Receipt Documents')

    @api.onchange('rules_company_id')
    def onchange_rules_company_id(self):
        super(ResConfigSettings, self).onchange_rules_company_id()
        if self.rules_company_id:
            if self.rules_company_id.send_receipt_and_payment:
                self.ps_is_send_payment = True
            else:
                self.ps_is_send_payment = False

    # 在保存时执行execute函数
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.ps_is_send_payment:
            vals = {
                'send_receipt_and_payment': True if self.ps_is_send_payment else False,
            }
        else:
            vals = {
                'send_receipt_and_payment': True if self.ps_is_send_payment else False,
            }
        if not self.module_inter_company_rules:
            vals = {
                'send_receipt_and_payment': False,
            }
        self.env.user.company_id.write(vals)
