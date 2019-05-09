# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2011 Cubic ERP - Teradata SAC. (http://cubicerp.com)

{
    'name': 'Argentina - Accounting Reports',
    'version': '1.1',
    'description': """
Accounting reports for Argentina
================================

    """,
    'author': ['Cubic ERP'],
    'website': 'http://cubicERP.com',
    'category': 'Accounting',
    'depends': ['l10n_ar', 'account_reports'],
    'data':[
        'data/account_financial_html_report_data.xml'
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
