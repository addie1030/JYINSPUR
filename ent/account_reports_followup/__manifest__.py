# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Follow-up Management',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
Module to automate letters for unpaid invoices, with multi-level recalls.
=========================================================================

You can define your multiple levels of recall through the menu:
---------------------------------------------------------------
    Configuration / Follow-up / Follow-up Levels
    
Once it is defined, you can automatically print recalls every day through simply clicking on the menu:
------------------------------------------------------------------------------------------------------
    Payment Follow-Up / Send Email and letters

It will generate a PDF / send emails / set manual actions according to the the different levels 
of recall defined. You can define different policies for different companies. 

""",
    'website': 'https://www.odoo.com/page/billing',
    'depends': ['account', 'mail', 'account_reports'],
    'data': [
        'security/account_followup_security.xml',
        'security/ir.model.access.csv',
        'data/account_followup_data.xml',
        'views/account_followup_views.xml',
        'views/res_config_settings_views.xml',
        'views/report_followup.xml',
    ],
    'qweb': [
        'static/src/xml/account_reports_followup_template.xml',
    ],
    'demo': ['data/account_followup_demo.xml'],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
