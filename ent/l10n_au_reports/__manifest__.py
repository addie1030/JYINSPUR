# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2015 Willow IT Pty Ltd (<http://www.willowit.com.au>).

{
    'name': 'Australian - Accounting Reports',
    'version': '1.1',
    'category': 'Accounting',
    'description': """
Australian Accounting Reports
=============================

GST Reporting for Australian Accounting.
    """,
    'author': 'Richard deMeester - Willow IT',
    'website': 'http://www.willowit.com',
    'depends': ['l10n_au',
                'account_reports'],
    'data': [
        'data/account_financial_html_report_data.xml',
     ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'images': [],
    'license': 'OEEL-1',
}
