# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.tools import misc, config

WEBSITE = "https://www.mypscloud.com"

class publisher_warranty_contract(models.AbstractModel):
    _inherit = "publisher_warranty.contract"

    @api.model
    def update_notification(self, cron_mode=True):
        module_ids = self.env['ir.module.module'].search([('name', 'in', ['saas_trial'])])
        # if module list have saas_trial ,ignore modification
        if module_ids:
            return super(publisher_warranty_contract, self).update_notification(cron_mode)

        # saas endpoint call
        config['publisher_warranty_url'] = WEBSITE + '/publisher-warranty/'
        return super(publisher_warranty_contract, self).update_notification(cron_mode)

