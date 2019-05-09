# -*- coding: utf-8 -*-
{
    'name': 'PS Cloud 库存',
    'version': '11.0.1.0',
    'summary': 'PS Cloud 库存',
    'description': """
        仓库人员在查看产品库存时需要系统首先过滤掉虚拟库位，避免虚拟库位中的数量影响统计结果 \n
        仓库人员需要在查看库存调拨记录时需要看到价格和金额两个字段以便了解库存移动金额 \n
        基于入库单生成退货单取原入库单单价(order_price) \n
        基于出库单生成退货单取原出库单单价(order_price)\n
        实现将一种/组物料转换成其他的一种/组其物料，数量 灵活输入，从而不使用繁琐的制造功能""",
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Warehouse',
    'depends': ['stock', ],
    'license': 'OEEL-1',
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/ps_stock_views.xml',
        'views/ps_stock_conversion_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}