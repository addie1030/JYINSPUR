# -*- coding: utf-8 -*-
{
    'name': "会计中心",
    'version': '12.0.1.0',
    'summary': "PS Cloud 财务会计中心",
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Accounting',
    'license': 'OEEL-1',
    'depends': ['ps_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/tree_view_asset.xml',
        'views/res_partner_company_setting_views.xml',
    ],
    'qweb': ["static/src/xml/*.xml"],
    'js': ["static/src/js/*.js"],
    'css': ["static/src/css/*.css"],
    'installable': True,
    'application': True,
    'auto_install': False,
}