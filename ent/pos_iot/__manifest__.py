# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': '',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Link your PoS configuration with an IoT Box',
    'description': """
It links the module 
""",
    'data': ['views/pos_config_views.xml',],
    'depends': ['point_of_sale', 'iot'],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
