# -*- coding: utf-8 -*-
{
    'name': "PS Cloud 销售合同",
    'version': '12.0.1.0',
    'summary': "PS Cloud 销售合同",
    'description':
        """
        为销售人员提供的可管理长期订单的销售合同
        对于长期订单，只有在收到客户的确切要货信息时，才能确定交货的数量和日期；合同也将用于预收客户预付款的依据，
        因此，需要一个业务流程来管理这种业务场景。
            
        """,
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Sales',
    'depends': ['base', 'sale', 'ps_sale'],
    'license': 'OEEL-1',
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/ps_advances_received_views.xml',
        'wizard/ps_contract_sales_order_views.xml',
        'views/ps_sale_contract_view.xml',
    ],
    'demo': [
        'demo/sale_contract_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
