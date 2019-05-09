# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': '付款单推送',
    'version': '12.0.1.0',
    'summary': 'PS Cloud 付款单推送',
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Productivity',
    'license': 'OEEL-1',
    'depends': ['inter_company_rules', 'ps_account'],
    'data': [
        'views/ps_res_config_settings.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    # 'post_init_hook': 'post_init_hook',
    # 'uninstall_hook': "uninstall_hook",
}