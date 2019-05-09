# -*- coding: utf-8 -*-
{
    'name': "Leaves Gantt",
    'summary': """Gantt view for Leaves Dashboard""",
    'description': """
    Gantt view for Leaves Dashboard
    """,
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['hr_holidays', 'web_gantt'],
    'auto_install': True,
    'data': [
        'views/hr_holidays_gantt_view.xml',
    ],
    'license': 'OEEL-1',
}
