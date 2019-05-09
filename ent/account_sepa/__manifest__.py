# -*- coding: utf-8 -*-
{
    'name': "SEPA Credit Transfer",
    'summary': """Export payments as SEPA Credit Transfer files""",
    'category': 'Accounting',
    'description': """
        Generate payment orders as recommended by the SEPA norm, thanks to pain.001 messages. Supported pain version (countries) are pain.001.001.03 (generic), pain.001.001.03.ch.02 (Switzerland) and pain.001.003.03 (Germany). The generated XML file can then be uploaded to your bank.

        This module follow the implementation guidelines issued by the European Payment Council.
        For more informations about the SEPA standards : http://www.iso20022.org/ and http://www.europeanpaymentscouncil.eu/
    """,
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['account_batch_payment', 'base_iban'],
    'data': [
        'data/sepa.xml',
        'views/account_journal_dashboard_view.xml',
        'views/res_config_settings_views.xml',
        'views/account_payment.xml',
    ],
    'license': 'OEEL-1',
}
