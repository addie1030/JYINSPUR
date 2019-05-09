# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2009 - now Grzegorz Grzelak grzegorz.grzelak@openglobe.pl

{
    'name': 'Poland - Accounting Reports',
    'version': '1.1',
    'description': """
Accounting reports for Poland
================================
    """,
    'author': ['Grzegorz Grzelak (OpenGLOBE)'],
    'category': 'Accounting',
    'depends': ['l10n_pl', 'account_reports'],
    'data': [
        'data/account_financial_html_report_data.xml'
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
