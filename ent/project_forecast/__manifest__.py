# -*- coding: utf-8 -*-
{
    'name': "Forecast",
    'summary': """Forecast your resources on project tasks""",
    'description': """
    Schedule your teams across projects and estimate deadlines more accurately.
    """,
    'category': 'Project',
    'version': '1.0',
    'depends': ['project', 'web_grid', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/project_forecast_security.xml',
        'views/project_forecast_views.xml',
        'views/project_views.xml',
        'views/res_config_settings_views.xml',
        'data/project_forecast_data.xml',
    ],
    'demo': [
        'data/project_forecast_demo.xml',
    ],
    'application': True,
    'license': 'OEEL-1',
}
