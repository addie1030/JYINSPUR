# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Timesheet and Forecast',
    'version': '1.0',
    'category': 'Hidden',
    'sequence': 50,
    'summary': 'Compare timesheets and forecasts',
    'depends': ['hr_timesheet', 'project_forecast'],
    'description': """
Compare timesheets and forecasts
================================

Better plan your futur forecasts by observing the number of hours pressed
on old forecasts.

""",
    'data': [
        'report/timesheet_forecast_report_views.xml',
        'security/ir.model.access.csv',
        'data/project_timesheet_forecast_data.xml',
        'views/project_forecast_views.xml',
    ],
    'auto_install': True,
}
