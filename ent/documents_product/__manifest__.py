# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Documents - Product',
    'version': '1.0',
    'category': 'Uncategorized',
    'summary': 'Products from Documents',
    'description': """
Add the ability to create products from the document module.
and to get the option to send products' attachments to the documents app.
""",
    'website': ' ',
    'depends': ['documents', 'product'],
    'data': ['data/data.xml', 'views/documents_views.xml'],
    'installable': True,
    'auto_install': True,
}
