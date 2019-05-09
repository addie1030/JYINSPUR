# -*- coding: utf-8 -*-
{
    'name': "account_online_sync",
    'summary': """
        This module is used for Online bank synchronization.""",

    'description': """
        This module is used for Online bank synchronization. It provides basic methods to synchronize bank statement.
    """,

    'category': 'Accounting',
    'version': '2.0',
    'depends': ['account'],

    'data': [
        'security/ir.model.access.csv',
        'views/online_sync_views.xml',
    ],
    'qweb': [
        'views/online_sync_templates.xml',
    ],
    'license': 'OEEL-1',
    'auto_install': True,
}
