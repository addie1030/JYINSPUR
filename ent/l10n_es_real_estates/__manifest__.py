# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "l10n_es_real_estates",
    'description': """
        This module adds support for real estates data to Spanish localization,
        and its mod 347 report.
    """,

    'category': 'Accounting',
    'version': '0.1',
    'depends': ['l10n_es_reports'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice_views.xml',
        'views/real_estates_data_views.xml',
        'wizard/aeat_boe_export_wizards.xml',
        'data/mod347.xml',
    ],
}
