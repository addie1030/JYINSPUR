# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) conexus.at

{
    'name': 'Austria - Accounting',
    'version': '1.0',
    'author': 'conexus.at',
    'website': 'http://www.conexus.at',
    'category': 'Accounting',
    'depends': ['l10n_at', 'account_reports'],
    'description': """
This module provides the standard Accounting Chart for Austria which is based on the Template from BMF.gv.at.
============================================================================================================= 
Please keep in mind that you should review and adapt it with your Accountant, before using it in a live Environment.
""",
    'demo': [],
    'data': ['data/account_financial_html_report_data.xml'],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
