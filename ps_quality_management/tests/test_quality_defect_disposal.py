# # -*- coding:utf-8 -*-
# import logging
#
# from odoo.exceptions import UserError
# from odoo.tests.common import TransactionCase
#
# _logger = logging.getLogger(__name__)
#
#
# class TestQualityDefectDisposal(TransactionCase):
#     def setUp(self):
#         super(TestQualityDefectDisposal, self).setUp()
#         user = self.env['res.users'].with_context(no_reset_password=True)
#         self.quality_user = user.create({
#             'name': 'Test Manager',
#             'login': 'manager',
#             'email': 'a.m@example.com',
#             'groups_id': [(6, 0, [self.env.ref('quality.group_quality_user').id])]
#         })
#         stock_picking_type = self.env['stock.picking.type'].search('id', '=', )
#         self.quality_defect_disposal_obj = self.env['ps.quality.defect.disposal']
#         self.quality_defect_disposal = self.quality_defect_disposal_obj.create({
#             'type_id': '',
#             'document': '',
#             'comments': '',
#             'warehouse_id': '',
#             'quality_check_id': '',
#             'quality_defect_disposal_line_ids': [(0, 0, {
#                 'product_id': '',
#                 'partner_id': '',
#                 'workshop_id': '',
#                 'operation_id': '',
#                 'lot_id': '',
#                 'decision_check_id': '',
#                 'qty_ng': '',
#                 'decision_id': '',
#                 'qty': '',
#             })]
#         })
#
#     def test_action_close(self):
#        pass
