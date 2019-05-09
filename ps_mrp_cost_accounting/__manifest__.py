# -*- coding: utf-8 -*-
{
    'name': "PS Cloud 生产成本核算",

    'summary': """
        PS Cloud 生产成本核算""",

    'description': """
        
    """,

    'author': "www.mypscloud.com",
    'website': "https://www.mypscloud.com/",

    'category': 'Account',
    'version': '12.0.1.0',

    'depends': ['stock', 'mrp', 'ps_account'],
    'qweb': ['static/src/xml/ps_mrp_expenses_pull_button.xml',
             ],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/menu_views.xml',
        'views/ps_mrp_cost_accounting.xml',
        'views/ps_mrp_cost_allocation.xml',
        'views/ps_mrp_expenses_plan_pull.xml',
        'views/ps_mrp_expense_item.xml',
        'views/ps_mrp_cost_item.xml',
        'views/ps_mrp_expenses_standard.xml',
        'views/ps_mrp_expenses_pull.xml',
        'wizard/ps_mrp_expenses_plan_pull_wizard.xml',
        'views/ps_mrp_expenses_standard_setting.xml',
        'views/ps_mrp_inventory.xml',
        'wizard/ps_mrp_inventory_wizard.xml',
        'views/ps_mrp_invest_yield_collection.xml',
        'wizard/ps_mrp_invest_yield_collection_wizard.xml',
        'wizard/ps_mrp_complete_warehouse_qty_wizard.xml',
        'views/ps_mrp_complete_warehouse_qty.xml',
        'wizard/ps_mrp_cost_allocation_wizard.xml',
        # 'views/ps_mrp_in_product_cost_calculation.xml',  # 在产品计算
        'wizard/ps_mrp_in_product_cost_calculation_wizard.xml',
    ],
    'js': ['static/src/js/*.js'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
