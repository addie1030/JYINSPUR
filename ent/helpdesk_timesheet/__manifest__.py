# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Helpdesk Timesheet',
    'category': 'Helpdesk',
    'summary': 'Project, Tasks, Timesheet',
    'depends': ['helpdesk', 'hr_timesheet'],
    'description': """
        - Allow to set project for Helpdesk team
        - Track timesheet for task from ticket
    """,
    'data': [
        'security/ir.model.access.csv',
        'security/helpdesk_timesheet_security.xml',
        'views/helpdesk_views.xml',
        'views/project_views.xml'
    ],
}
