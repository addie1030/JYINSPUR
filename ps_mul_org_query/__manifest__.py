# -*- coding: utf-8 -*-
{
    'name': "PS Cloud 组织间结算查询分析",

    'summary': """
        PS Cloud 组织间结算查询分析""",

    'description': """

    """,

    'author': "www.mypscloud.com",
    'website': "https://www.mypscloud.com/",

    'category': 'Tools',
    'version': '11.0.1.0',

    'depends': [],

    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/ps_sale_invoice_analysis.xml',
        'views/ps_sale_order_analysis.xml',
    ],
    'application': False,
}
