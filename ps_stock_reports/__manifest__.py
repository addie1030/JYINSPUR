# -*- coding: utf-8 -*-
{
    'name': 'PS Cloud 库存报表',
    'version': '12.0.1.0',
    'summary': 'PS Cloud 库存报表',
    'description': """
        分析指定时间范围内，指定仓库的收发情况
       """,
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Warehouse',
    'depends': ['stock', 'ps_sale', 'ps_purchase'],
    'license': 'OEEL-1',
    'data': [
        'security/ir.model.access.csv',
        'wizard/ps_wizard_stock_price_dispatch.xml',
        'views/ps_stock_price_dispatch.xml',

    ],
    'demo': [
        'demo/stock_move_demo.xml'
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
