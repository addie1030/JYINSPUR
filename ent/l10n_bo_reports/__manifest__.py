# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2011 Cubic ERP - Teradata SAC. (https://cubicerp.com).

{
    "name": "Bolivia - Accounting Reports",
    "version": "1.1",
    "description": """
Accounting reports for Bolivia
================================

    """,
    "author": "Cubic ERP",
    "website": "https://cubicERP.com",
    'category': 'Accounting',
    "depends": ["l10n_bo", 'account_reports'],
    "data": [
        "data/account_financial_html_report_data.xml",
    ],
    "auto_install": True,
    "installable": True,
    "license": "OEEL-1",
}
