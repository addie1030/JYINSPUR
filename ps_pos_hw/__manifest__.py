# -*- coding: utf-8 -*-
{
    'name': 'POS Electron Hardware Driver',
    'version': '12.0.1.0',
    'category': 'Point of Sale',
    'sequence': 13,
    'summary': 'POS Electron Hardware Driver',
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'depends': ['ps_pos'],
    'license': 'OEEL-1',
    'data': [
            'data/sequence.xml',
            'views/ps_pos_hw_templates.xml',
            'wizard/card_read_wizard.xml',
            'wizard/card_manage_wizard.xml',
        ],
    'qweb': [
            "static/src/xml/inherit_pos.xml",
        ],
    'js': ["static/src/js/*.js"],
    'css': ["static/src/css/*.css"],
    'installable': True,
    'auto_install': False,
}
