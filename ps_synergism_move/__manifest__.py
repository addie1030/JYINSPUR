# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': '协同凭证',
    'version': '1.1',
    'summary': 'Synergism Account Move',
    'sequence': 30,
    'description': """
            Synergism Account Move.
    """,
    'category': 'Accounting',
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'depends': ['ps_account'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/ps_synergism_move_wizard.xml',
        'views/ps_synergism_move.xml',
        'views/ps_account_trade.xml',
        'security/ir.rule.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False
}
