# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Stock enterprise",
    'version': "1.0",
    'category': "Stock",
    'summary': "Advanced features for Stock",
    'description': """
Contains the enterprise views for Stock management
    """,
    'depends': ['stock', 'web_dashboard', 'web_cohort'],
    'data': [
        'security/ir.model.access.csv',

        'report/stock_report_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
