# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Romania - Accounting Reports',
    'version': '1.1',
    'category': 'Accounting',
    'author': 'ERPsystems Solutions',
    'description': """
        Accounting reports for Romania
    """,
    'depends': [
        'l10n_ro', 'account_reports',
    ],
    'data': [
        'data/account_financial_html_report_data.xml',
    ],
    'installable': True,
    'auto_install': True,
    'website': 'http://www.erpsystems.ro',
    'license': 'OEEL-1',
}
