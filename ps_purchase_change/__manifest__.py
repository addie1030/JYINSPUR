# -*- coding: utf-8 -*-
{
    'name': "PS Cloud Purchase Change(PS Cloud采购订单变更)",
    'version': '12.0.1.0',
    'summary': "PS Cloud采购订单变更",
    'description':"""
        采购订单是企业与供应商进行商品和服务采购的合法凭据，是采购业务管理的核心。\n
        由于客户需求变化或计划变化或工程变更等种种原因，采购订单在执行过程中需要进行变更，\n
        并且必须将订单变更通知供应商及时调整生产和交货计划，以确保能够正常供应货物，满足企业生产需要。""",
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Purchases',
    'depends': ['purchase', 'stock_account', ],
    'license': 'OEEL-1',
    'data': [
        'security/ir.model.access.csv',
        # 'security/ir_rule.xml',
        'views/purchase_order_change_view.xml',
        'data/ps_purchase_change_data.xml',
        # 'views/ps_config.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}