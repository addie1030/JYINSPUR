# -*- coding: utf-8 -*-

{
    'name': "Delivery Barcode Scanning",
    'summary': "Add barcode scanning facilities to Delivery.",
    'description': """
        This module adds support for barcodes scanning to the delivery packages.
    """,
    'version': '1.0',
    'depends': ['stock_barcode', 'delivery'],
    'data': [
        'views/delivery_barcode_templates.xml',
        'views/stock_picking_views.xml',
        ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
