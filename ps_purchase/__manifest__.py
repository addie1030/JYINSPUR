# -*- coding: utf-8 -*-
{
    'name': "PS Cloud 采购",
    'version': '12.0.1.0',
    'summary': "PS Cloud 采购",
    'description':"""
        仓库人员在收货时需要系统自动检查是否超过采购订单数量避免误操作输入错误的已收数量 \n
        采购人员随时查看采购订单明细记录以便了解各个产品历史采购情况 \n
        采购订单生成入库单传给入库单行含税单价""",
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Purchases',
    'depends': ['purchase', 'ps_stock', ],
    'license': 'OEEL-1',
    'data': [
        'views/ps_purchase_order_line_view.xml',
        'views/ps_config.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}