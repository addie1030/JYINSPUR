# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

from .taxcloud_request import TaxCloudRequest

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        if self.fiscal_position_id.is_taxcloud:
            self.validate_taxes_on_sales_order()
        return super(SaleOrder, self).action_confirm()

    @api.multi
    def validate_taxes_on_sales_order(self):
        company = self.company_id
        Param = self.env['ir.config_parameter']
        api_id = Param.sudo().get_param('account_taxcloud.taxcloud_api_id_{}'.format(company.id)) or Param.sudo().get_param('account_taxcloud.taxcloud_api_id')
        api_key = Param.sudo().get_param('account_taxcloud.taxcloud_api_key_{}'.format(company.id)) or Param.sudo().get_param('account_taxcloud.taxcloud_api_key')
        request = TaxCloudRequest(api_id, api_key)

        shipper = self.company_id or self.env.user.company_id
        request.set_location_origin_detail(shipper)
        request.set_location_destination_detail(self.partner_shipping_id)

        request.set_order_items_detail(self)

        response = request.get_all_taxes_values()

        if response.get('error_message'):
            raise ValidationError(_('Unable to retrieve taxes from TaxCloud: ')+'\n'+response['error_message']+'\n\n'+_('The configuration of TaxCloud is in the Accounting app, Settings menu.'))

        tax_values = response['values']

        for index, line in enumerate(self.order_line):
            if line.price_unit >= 0.0 and line.product_uom_qty >= 0.0:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0) * line.product_uom_qty
                if not price:
                    tax_rate = 0.0
                else:
                    tax_rate = tax_values[index] / price * 100
                if len(line.tax_id) != 1 or float_compare(line.tax_id.amount, tax_rate, precision_digits=3):
                    tax_rate = float_round(tax_rate, precision_digits=3)
                    tax = self.env['account.tax'].with_context(active_test=False).sudo().search([
                        ('amount', '=', tax_rate),
                        ('amount_type', '=', 'percent'),
                        ('type_tax_use', '=', 'sale'),
                        ('company_id', '=', company.id),
                    ], limit=1)
                    if not tax:
                        tax = self.env['account.tax'].sudo().create({
                            'name': 'Tax %.3f %%' % (tax_rate),
                            'amount': tax_rate,
                            'amount_type': 'percent',
                            'type_tax_use': 'sale',
                            'description': 'Sales Tax',
                            'company_id': company.id,
                        })
                    line.tax_id = tax
        return True
