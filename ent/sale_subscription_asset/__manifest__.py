# -*- coding: utf-8 -*-

{
    'name': 'Deferred Revenues Management for Subscriptions',
    'version': '1.0',
    'category': 'Sales',
    'description': """
This module allows you to set a deferred revenue on your subscriptions.
""",
    'depends': ['sale_subscription', 'account_deferred_revenue'],
    'data': [
        'views/sale_subscription_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
