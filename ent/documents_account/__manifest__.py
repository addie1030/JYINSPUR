# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Documents - Accounting',
    'version': '1.0',
    'category': 'Uncategorized',
    'summary': 'Invoices from Documents',
    'description': """
Add the ability to create invoices from the document module.
""",
    'website': ' ',
    'depends': ['documents', 'account'],
    'data': ['data/data.xml', 'views/documents_views.xml'],
    'installable': True,
    'auto_install': True,
}
