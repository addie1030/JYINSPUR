# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Project Enterprise",
    'summary': """Bridge module for project and enterprise""",
    'description': """
Bridge module for project and enterprise
    """,
    'category': 'Project',
    'version': '1.0',
    'depends': ['project'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'auto_install': True,
    'license': 'OEEL-1',
}
