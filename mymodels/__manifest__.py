# -*- coding: utf-8 -*-
{
    'name': "jyinspur",

    'summary': """
        jyinspur""",

    'description': """
        jyinspur
    """,

    'author': "jyinspur",
    'website': "jyinspur.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        
        'views/views.xml',
        
    ],
    # only loaded in demonstration mode
   # 'demo': [
    #    'demo/demo.xml',
    #],
}