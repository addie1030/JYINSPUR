# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError,Warning


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ps_is_overpass_initial_ordered_process = fields.Boolean(string='Not Exceeding Receive/Return',
                                                            help="Whether processing more than initial ordered is permitted or not")# 判断是否允许超量收货/退货
    module_ps_purchase_change = fields.Boolean(string='Purchase Order Change',
                                                            help="Allow change purchase order with a traceable record")# 判断是否允许变更采购订单

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.user.company_id.ps_is_overpass_initial_ordered_process = self.ps_is_overpass_initial_ordered_process

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            ps_is_overpass_initial_ordered_process=self.env.user.company_id.ps_is_overpass_initial_ordered_process,
        )
        return res

    @api.onchange('module_ps_purchase_change')
    def onchange_po_lock(self):
        if not self.module_ps_purchase_change:
            self.lock_confirmed_po = False
            self.po_lock = 'edit'
        elif self.module_ps_purchase_change:
            self.lock_confirmed_po = True
            self.po_lock = 'lock'

class PsResCompany(models.Model):
    _inherit = 'res.company'

    ps_is_overpass_initial_ordered_process = fields.Boolean()  # 判断是否允许超量收货


