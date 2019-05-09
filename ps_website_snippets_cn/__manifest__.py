# -*- coding: utf-8 -*-
{
    'name': "网站区块标题中文",

    'summary': """
        Replace the snippets name on website editor with Chinese""",

    'description': """
        网站编辑器中文补丁
    """,

    'author': "www.mypscloud.com",
    'website': "http://www.mypscloud.com",

    'category': 'Hidden',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['website'],

    'data': [
        'views/ir.ui.view.csv',
    ],

    'auto_install': True,
}