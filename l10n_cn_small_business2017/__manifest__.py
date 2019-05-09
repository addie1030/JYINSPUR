# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': '2017中国小企业会计科目表',
    'version': '1.0',
    'category': 'Localization',
    'author': 'sunny',
    'maintainer': '',
    'website': 'www.mypscloud.com',
    'description': """

    2017中国小企业会计科目表

    """,
    'depends': ['l10n_cn'],
    'data': [
        'data/l10n_cn_small_business2017_chart_data.xml',
        'data/account_chart_template_business2017.xml',
        # 'data/account_account_2017_data.xml',
    ],
    'installable': True,
    'auto_install': False
}
