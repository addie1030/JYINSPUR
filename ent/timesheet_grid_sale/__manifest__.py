# -*- coding: utf-8 -*-
{
    'name': "Sales Timesheet: Grid Support",

    'summary': "Configure timesheet invoicing",

    'description': """
        When invoicing timesheets, allows invoicing either all timesheets
        linked to an SO, or only the validated timesheets
    """,

    'category': 'Hidden',
    'version': '0.1',

    'depends': ['sale_timesheet', 'timesheet_grid'],
    'data': [
        'views/res_config_settings_views.xml'
    ],

    'auto_install': True,
    'license': 'OEEL-1',
}
