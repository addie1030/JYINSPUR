# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError,Warning


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_sale_price_change = fields.Boolean("Enable Price Change Order",
                                             implied_group='ps_sale.group_price_change_user')

    ps_is_overpass_initial_ordered_sale = fields.Boolean(string='Not Exceeding Sale/Return',
                                                            help="Whether processing more than initial ordered is permitted or not")# 判断是否允许超量发货/退货

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.user.company_id.ps_is_overpass_initial_ordered_sale = self.ps_is_overpass_initial_ordered_sale


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            ps_is_overpass_initial_ordered_sale=self.env.user.company_id.ps_is_overpass_initial_ordered_sale
        )
        return res


class PsResCompany(models.Model):
    _inherit = 'res.company'

    ps_is_overpass_initial_ordered_sale = fields.Boolean()  # 判断是否允许超量发货/发货退回


