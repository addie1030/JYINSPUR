# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'EDI External Trade Complement for Mexico',
    'version': '0.1',
    'category': 'Hidden',
    'summary': 'External Trade Complement for the Mexican localization',
    'depends': [
        'l10n_mx_edi',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/1.1/external_trade.xml',
        'data/product_data.xml',
        'views/account_invoice_view.xml',
        'views/report_invoice.xml',
        'views/res_partner_view.xml',
        'views/res_config_settings_views.xml',
        'views/product_view.xml',
        'views/res_company_view.xml',
        'views/res_city_view.xml',
    ],
    'demo': [
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
