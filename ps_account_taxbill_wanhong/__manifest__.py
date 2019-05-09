# -*- coding: utf-8 -*-
{
    'name': "PS Cloud Tax bill wanhong（万鸿税票接口管理）",
    'version': '12.0.1.0',
    'summary': "PS Cloud Tax bill wanhong（PS Cloud万鸿税票接口）",
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Accounting',
    'license': 'OEEL-1',
    'depends': ['ps_account_taxbill'],
    'data': [
        'security/ir.model.access.csv',
        'views/ps_account_taxbill_register.xml',
        'views/ps_account_taxbill.xml',
        'views/ps_account_invoice_taxbill_display.xml',
        'wizard/ps_res_company_wizard.xml',
        'wizard/ps_apply_vat_wizard.xml',
    ],
    'demo': [
        'data/res_company_demo.xml',
        'demo/taxbill_wanhong_demo.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}