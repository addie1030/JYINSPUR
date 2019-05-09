# -*- coding: utf-8 -*-
{
    'name': "PS Cloud 销售",
    'version': '12.0.1.0',
    'summary': "PS Cloud 销售",
    'description':"""
        销售人员随时查看销售订单明细记录用于以便了解各个产品历史销售情况 \n
        销售订单生成出库单传给出库单行含税单价""",
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Sales',
    'depends': ['sale_stock', 'ps_stock', 'sale_management'],
    'license': 'OEEL-1',
    'data': [
        'data/sequence.xml',
        'demo/product_pricelist_change_demo.xml',
        'security/ir.model.access.csv',
        'security/ps_sale_security.xml',
        'views/ps_config.xml',
        'views/ps_pricelist.xml',
        'views/ps_sale_order_line_view.xml',
        'views/ps_config_pricelist.xml',
        'views/ps_product_pricelist_change.xml',
        'views/ps_pricelist_product.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}