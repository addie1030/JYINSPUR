# -*- encoding: utf-8 -*-
{
    'name': 'Predictive vendor bill data',
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['account_accountant'],
    'description': """Let the system try to select the right account and/or product for your vendor bills""",
    'data': ['views/account_invoice_view.xml'],
    'auto_install': True,
}
