# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'IoT features for Work Order Quality Control',
    'version': '1.0',
    'category': 'Manufacturing',
    'sequence': 50,
    'summary': 'Quality steps in MRP work orders with IoT devices',
    'depends': ['quality_mrp_workorder', 'iot'],
    'description': """
    Configure IoT devices to be used in certain 
    quality steps for taking measures, taking pictures, ...
""",
    "data": [
        'views/mrp_workorder_views.xml',
    ],
    'auto_install': True,
    'license': 'OEEL-1',
}
