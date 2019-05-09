# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2011 Smartmode LTD (<http://www.smartmode.co.uk>).

{
    'name': 'UK - Accounting Reports',
    'version': '1.1',
    'category': 'Accounting',
    'description': """
        Accounting reports for UK
    """,
    'author': 'SmartMode LTD',
    'website': 'http://www.smartmode.co.uk',
    'depends': [
        'l10n_uk', 'account_reports'
    ],
    'data': [
        'data/account_financial_html_report_data.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
