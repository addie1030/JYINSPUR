# -*- coding: utf-8 -*-
{
    'name': "PS Cloud Tax bill manage（税票管理）",
    'version': '12.0.1.0',
    'summary': "PS Cloud Tax bill application（PS Cloud税票管理）",
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Accounting',
    'license': 'OEEL-1',
    'depends': ['account'],
    'data': [
        'security/ps_account_taxbill_security.xml',
        'security/ir.model.access.csv',
        'data/ps_account_taxbill_data.xml',
        'data/res_bank_data.xml',
        'data/res_company_data.xml',
        'views/ps_account_taxbill_menuitem.xml',
        'views/ps_account_taxbill.xml',
        'views/ps_account_taxbill_config.xml',
        'views/ps_partner.xml',
    ],
    'demo': [
        'data/res_company_demo.xml',
    ],
    'js': ["static/src/js/*.js"],
    'installable': True,
    'application': True,
    'auto_install': False,
}