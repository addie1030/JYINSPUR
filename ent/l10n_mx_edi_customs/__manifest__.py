# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo Mexico Localization for Invoice with customs Number',
    'summary': '''
        Generate Electronic Invoice with Customs Number
    ''',
    'version': '0.1',
    'category': 'Hidden',
    'license': 'OEEL-1',
    'depends': [
        'l10n_mx_edi',
    ],
    'data': [
        'views/invoice_view.xml',
        'views/l10n_mx_edi_report_invoice.xml',
        'data/customs_information.xml',
    ],
    'installable': True,
}
