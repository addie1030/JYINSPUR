# -*- coding: utf-8 -*-
{
    'name': "Zebra printers integration for MRP",

    'summary': """
        Zebra printers integration for mrp module""",

    'description': """
        MRP extention of ability to print labels on Zebra thermal printers.
    """,

    'author': "Odoo SA",
    'website': "https://www.odoo.com",

    # for the full list
    'category': 'mrp',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['stock_zebra', 'quality_mrp_iot'],
    'auto_install': True,

    # always loaded
    'data': [
        'views/mrp_workorder_views.xml',

        'report/mrp_production_templates.xml',
        'report/mrp_production_reports.xml',

        'data/quality_point.xml',
    ],
    'demo': [
        'data/quality_demo.xml'
    ]

}
