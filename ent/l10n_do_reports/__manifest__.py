# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# First author: Jose Ernesto Mendez <tecnologia@obsdr.com> (Open Business Solutions SRL.)
# Copyright (c) 2012 -TODAY Open Business Solutions, SRL. (http://obsdr.com). All rights reserved.
# This is a fork to upgrade to odoo 8.0
# by Marcos Organizador de Negocios - Eneldo Serrata - www.marcos.org.do

{
    'name': 'Dominican Republic - Accounting',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
This is the base module to manage the accounting chart for Dominican Republic.
==============================================================================

* Chart of Accounts.
* The Tax Code Chart for Domincan Republic
* The main taxes used in Domincan Republic
* Fiscal position for local """,
    'author': 'Eneldo Serrata - Marcos Organizador de Negocios, SRL.',
    'website': 'http://marcos.do',
    'depends': ['l10n_do', 'account_reports'],
    'data': [
        'data/account_financial_html_report_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
