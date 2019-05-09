# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2010 kazacube (http://kazacube.com).

{
    'name': 'Maroc - Accounting Reports',
    'version': '1.1',
    'description': """
Accounting reports for Maroc
================================
    """,
    'author': ['kazacube'],
    'website': 'http://www.kazacube.com',
    'category': 'Accounting',
    'depends': ['l10n_ma', 'account_reports'],
    'data': [
        'data/account_financial_html_report_data.xml'
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
