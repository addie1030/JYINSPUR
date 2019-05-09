# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'UK - Accounting Reports to HMRC',
    'version': '1.1',
    'category': 'Accounting',
    'description': """
        Accounting reports send to HMRC
    """,
    'depends': [
        'l10n_uk_reports'
    ],
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
        'security/hmrc_security.xml',
        'wizard/hmrc_send_wizard.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
