# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .taxcloud_request import TaxCloudRequest

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    taxcloud_api_id = fields.Char(string='TaxCloud API ID', default='', config_parameter='account_taxcloud.taxcloud_api_id')
    taxcloud_api_key = fields.Char(string='TaxCloud API KEY', default='', config_parameter='account_taxcloud.taxcloud_api_key')
    tic_category_id = fields.Many2one(related='company_id.tic_category_id', string="Default TIC Code", readonly=False)

    @api.multi
    def sync_taxcloud_category(self):
        Category = self.env['product.tic.category']
        request = TaxCloudRequest(self.taxcloud_api_id, self.taxcloud_api_key)
        res = request.get_tic_category()

        if res.get('error_message'):
            raise ValidationError(_('Unable to retrieve taxes from TaxCloud: ')+'\n'+res['error_message']+'\n\n'+_('The configuration of TaxCloud is in the Accounting app, Settings menu.'))

        for category in res['data']:
            if not Category.search([('code', '=', category['TICID'])], limit=1):
                Category.create({'code': category['TICID'], 'description': category['Description']})
        if not self.env.user.company_id.tic_category_id:
            self.env.user.company_id.tic_category_id = Category.search([('code', '=', 0)], limit=1)
        return True
