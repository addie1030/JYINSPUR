# -*- coding: utf-8 -*-

{
    'name': 'Deferred Revenues',
    'version': '1.0',
    'depends': ['account_asset'],
    'category': 'Accounting',
    'description': """

Revenue recognitions
====================
Manage revenue recognitions on product sales.
Keeps track of the revenue recognition installments, and creates corresponding journal entries.

    """,
    'website': 'https://www.odoo.com/page/accounting',
    'category': 'Accounting',
    'data': [
        'wizard/wizard_asset_compute_view.xml',
        'report/account_deferred_revenue_report_view.xml',
        'views/account_deferred_revenue.xml',
        'views/account_deferred_revenue_invoice_view.xml',
        'views/account_deferred_revenue_product_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OEEL-1',
}
