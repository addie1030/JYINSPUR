# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright: (C) 2012 - Mentis d.o.o., Dravograd

{
    'name': 'Slovenian - Accounting Reports',
    'version': '1.1',
    'author': 'Mentis d.o.o.',
    'website': 'https://www.mentis.si',
    'category': 'Accounting',
    'description': """
        Accounting reports for Slovenian
    """,
    'depends': ['l10n_si', 'account_reports'],
    'data': [
        'data/account_financial_html_report_data.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
