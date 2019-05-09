# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Marketing Automation",
    'version': "1.0",
    'summary': "Build automated mailing campaigns",
    'website': 'https://www.odoo.com/page/marketing-automation',
    'category': "Marketing",
    'depends': ['mass_mailing'],
    'data': [
        'security/marketing_automation_security.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/marketing_campaign_views.xml',
        'views/marketing_participant_views.xml',
        'views/mail_mass_mailing_views.xml',
        'data/marketing_automation_data.xml',
    ],
    'demo': [
        'data/marketing_automation_demo.xml'
    ],
    'application': True,
    'license': 'OEEL-1',
    'uninstall_hook': 'uninstall_hook',
}
