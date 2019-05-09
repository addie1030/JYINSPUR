# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) Rooms For (Hong Kong) Limited T/A OSCG

{
    'name': 'Japan - Accounting Reports',
    'version': '1.1',
    'description': """
Accounting reports for Japan
================================
    """,
    'author': ['Rooms For (Hong Kong) Limited T/A OSCG'],
    'website': 'http://www.openerp-asia.net/',
    'category': 'Accounting',
    'depends': ['l10n_jp', 'account_reports'],
    'data': [
        'data/account_financial_html_report_data.xml'
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
