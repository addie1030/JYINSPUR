# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'EDI for Mexico',
    'version': '0.1',
    'category': 'Hidden',
    'summary': 'Mexican Localization for EDI documents',
    'description': """
EDI Mexican Localization
========================
Allow the user to generate the EDI document for Mexican invoicing.

This module allows the creation of the EDI documents and the communication with the Mexican certification providers (PACs) to sign/cancel them.
    """,
    'depends': [
        'account',
        'account_cancel',
        'base_vat',
        'base_address_extended',
        'document',
        'base_address_city',
    ],
    'external_dependencies' : {
        'python' : ['OpenSSL'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/l10n_mx_edi_certificate.xml',
        'data/3.3/cfdi.xml',
        'data/3.3/payment10.xml',
        'data/account_data.xml',
        'data/action_server_data.xml',
        'data/payment_method_data.xml',
        'data/res_country_data.xml',
        'data/res_currency_data.xml',
        'data/res_partner_category.xml',
        'data/mail_invoice_template.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_view.xml',
        'views/account_menuitem.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/ir_ui_view_view.xml',
        'views/certificate_view.xml',
        "views/payment_method_view.xml",
        'views/account_view.xml',
        "views/l10n_mx_edi_report_invoice.xml",
        "views/l10n_mx_edi_report_payment.xml",
        'views/res_country_view.xml',
        'views/product_view.xml',
    ],
    'demo': [
        'demo/l10n_mx_edi_demo.xml',
        'views/addenda/bosh.xml',
        'views/addenda/autozone.xml',
        'demo/config_parameter_demo.xml',
    ],
    "post_init_hook": "post_init_hook",
    'installable': True,
    'auto_install': False,
}
