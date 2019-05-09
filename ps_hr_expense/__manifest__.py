# -*- coding: utf-8 -*-
{
    'name': "PS Cloud 费用申请",

    'summary': """
        PS Cloud 费用申请""",

    'description': """
        
    """,

    'author': "www.mypscloud.com",
    'website': "https://www.mypscloud.com/",

    'category': 'Expenses',
    'version': '11.0.1.0',

    'depends': ['hr_expense'],

    'data': [
        'security/ir.model.access.csv',
        'data/ps_expense_request_data.xml',
        'views/ps_expense_request.xml',
        'views/ps_expense_refund.xml',
        'wizard/ps_refund_wizard.xml',
        'views/ps_expense_request_application.xml',
        'views/ps_expense_views.xml',
        'report/ps_loan_analysis.xml',
    ],
    'application': False,
}
