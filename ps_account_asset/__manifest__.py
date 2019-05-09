# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': '资产管理',
    'version': '12.0.1.0',
    'summary': 'PS Cloud 资产管理',
    'author': "www.mypscloud.com",
    'website': 'https://www.mypscloud.com/',
    'category': 'Accounting',
    'license': 'OEEL-1',
    'depends': ['account_asset','ps_account'],
    'data': [
        'data/ps_asset_state_data.xml',
        'data/ps_asset_change_mode_data.xml',
        'data/ps_asset_inventory_data.xml',
        'data/ps_asset_disposal_data.xml',
        'data/ps_asset_alteration_data.xml',
        'security/ir.model.access.csv',
        'views/ps_account_asset.xml',
        'views/ps_asset_state_views.xml',
        'views/ps_asset_change_mode_views.xml',
        'views/ps_asset_location_views.xml',
        'views/ps_asset_category_views.xml',
        'views/ps_asset_inventory_views.xml',
        'views/ps_asset_disposal.xml',
        'views/ps_asset_alteration_views.xml',
        'reports/ps_depreciation_details_template.xml',
        'reports/ps_asset_analysis_template.xml',
        'wizard/ps_asset_depreciation_confirmation_wizard_views.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}