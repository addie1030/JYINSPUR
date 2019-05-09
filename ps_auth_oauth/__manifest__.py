# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': '浪潮通行证',
    'version': '12.0.1.0',
    'summary': '浪潮通行证',
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Tools',
    'license': 'OEEL-1',
    'depends': ['auth_oauth'],
    'data': [
        'views/auth_oauth_views.xml',
        'views/auth_oauth_login.xml',
    ],
    'qweb': [],
    'js': [],
    'css': [],
}
