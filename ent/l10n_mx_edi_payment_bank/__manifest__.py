# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Bank account payment to Mexico',
    'version': '0.1',
    'category': 'Hidden',
    'summary': 'Bank account in the payments',
    'description': """
EDI Mexican Localization
========================
Allow the user to select the bank account that was used the customer to paid the invoices.
    """,
    'depends': [
        'l10n_mx_edi',
    ],
    'data': [
        'views/account_view.xml',
        'views/account_payment_view.xml',
        'views/res_bank_view.xml',
    ],
    'installable': True,
    'auto_install': True,
}
