# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account Invoice Extract',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Extract data from invoice scans to fill them automatically',
    'depends': ['account_accountant', 'iap', 'mail_enterprise'],
    'data': [
        'security/ir.model.access.csv',
        'data/config_parameter_endpoint.xml',
        'data/extraction_status.xml',
        'data/res_config_settings_views.xml',
    ],
    'auto_install': True,
}
