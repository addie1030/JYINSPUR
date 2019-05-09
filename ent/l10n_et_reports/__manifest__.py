# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2012 Michael Telahun Makonnen <mmakonnen@gmail.com>.

{
    'name': 'Ethiopia - Accounting Reports',
    'version': '1.1',
    'description': """
Accounting reports for Ethiopia
================================

    """,
    'author': ['Michael Telahun Makonnen <mmakonnen@gmail.com>'],
    'website': 'http://miketelahun.wordpress.com',
    'category': 'Accounting',
    'depends': ['l10n_et', 'account_reports'],
    'data':[
        'data/account_financial_html_report_data.xml'
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
