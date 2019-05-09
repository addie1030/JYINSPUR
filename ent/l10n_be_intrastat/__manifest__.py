# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Belgian Intrastat Declaration',
    'category': 'Accounting',
    'description': """
Generates Intrastat XML report for declaration
Based on invoices.
    """,
    'depends': ['l10n_be', 'account_intrastat'],
    'data': [
        'data/code_region_data.xml',
        'data/intrastat_export.xml',
        'views/res_config_settings.xml',
    ],
    'auto_install': True,
}
