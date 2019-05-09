# -*- coding: utf-8 -*-
{
    'name': "PS Cloud BOM process version management（生产数据BOM工艺版本管理）",
    'version': '12.0.1.0',
    'summary': "PS Cloud BOM process version management（生产数据BOM工艺版本管理）",
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Manufacturing',
    'license': 'OEEL-1',
    'depends': ['ps_production_data', 'mrp_plm'],
    'data': [
        'security/ir.model.access.csv',
        'views/ps_mrp_bom.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}