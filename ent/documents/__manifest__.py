# -*- coding: utf-8 -*-
{
    'name': "Documents",

    'summary': "Document management",

    'description': """
        App to upload and manage your documents.
    """,

    'author': "Odoo",
    'category': 'Extra Tools',
    'version': '1.0',
    'application': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'portal', 'web'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'assets.xml',
        'data/documents_data.xml',
        'views/documents_views.xml',
        'views/templates.xml',
        'wizard/request_activity_views.xml',
    ],

    'qweb': [
        "static/src/xml/*.xml",
    ],

    'demo': [
        'demo/demo.xml',
    ],
}
