# -*- coding: utf-8 -*-
{
    'name': 'PS Quality Management',
    'version': '12.0.0',
    'summary': 'Manage Quality',
    'author': 'www.mypscloud.com',
    'website': 'https://www.mypscloud.com/',
    'license': 'OEEL-1',
    'depends': ['quality_control'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ps_quality_testing_aql_data.xml',
        'data/ps_quality_inspection_level_data.xml',
        'data/ps_quality_sampling_code_data.xml',
        'data/ps_quality_defect_consequence_data.xml',
        'data/ps_quality_decision.xml',
        'data/ps_quality_sampling_plan.xml',
        'data/ps_quality_sampling_plan_strict.xml',
        'data/ps_quality_sampling_plan_loose.xml',
        'views/ps_quality_alert_inherit.xml',
        'views/ps_quality_inventory_check_views.xml',
        'views/ps_quality_inventory_check_request_views.xml',
        'views/ps_quality_inspection_level_views.xml',
        'views/ps_quality_testing_aql_views.xml',
        'views/ps_quality_defect_disposal.xml',
        'views/ps_quality_testing_item_views.xml',
        'views/ps_quality_inspection_plan_views.xml',
        'views/ps_quality_product_template_views.xml',
        'views/ps_quality_production_lot_views.xml',
        'views/ps_quality_check_order_views.xml',
        'views/ps_quality_check_view.xml',
        'views/ps_quality_data_dict_views.xml',
        'views/ps_quality_control_point_inherit.xml',
        'views/ps_quality_inspection_plan_views.xml',
        'views/ps_quality_stock_warehouse_views.xml',
        'views/ps_stock_picking_views.xml',
        'views/ps_quality_sampling_plan_views.xml',
        'views/ps_quality_sampling_code_views.xml',
        'views/ps_quality_management_menu.xml',
        'views/templates.xml',
        'report/report_ps_quality_sampling_code.xml',
    ],
    'demo': [
        'demo/quality_stock_move_demo.xml',
        'demo/quality_inspection_level_demo.xml',
        'demo/quality_inventory_check_request_demo.xml',
        # 'demo/quality_testing_item_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,

    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
