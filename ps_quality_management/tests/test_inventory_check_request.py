# -*- coding: utf-8 -*-
from datetime import datetime
import logging

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestInventoryCheckRequest(TransactionCase):
    def setUp(self):
        super(TestInventoryCheckRequest, self).setUp()
        self.lot_id = self.env.ref('ps_quality_management.production_lot_1').id
        self.location_id = self.env.ref('stock.location_order').id
        self.product_id = self.env.ref('ps_quality_management.product_product_computer').id
        self.company_id = self.env.ref('base.main_company')
        self.picking_id = self.env.ref('ps_quality_management.quality_incoming_stock_move')

        user = self.env['res.users'].with_context(no_reset_password=True)
        self.quality_user = user.create({
            'name': 'Andrew Manager',
            'login': 'manager',
            'email': 'a.m@example.com',
            'groups_id': [(6, 0, [self.env.ref('quality.group_quality_user').id])]
        })

    def test_quality_inspection_level(self):
        # test the quality inspection level
        record1 = self.env['ps.quality.inspection.level'].search([('code', '=', 'S-1'), ('category', '=', 'special')])
        record2 = self.env['ps.quality.inspection.level'].search([('code', '=', 'S-2'), ('category', '=', False)])
        record3 = self.env['ps.quality.inspection.level'].search([('code', '=', False), ('category', '=', 'normal')])

        record1._spell_name()
        record2._spell_name()
        record3._spell_name()

        self.assertEqual(record1.name, 'special S-1', 'The name compute error!')
        self.assertEqual(record2.name, 'S-2', 'The name compute error!')
        self.assertEqual(record3.name, 'normal', 'The name compute error!')

    def test_inventory_inspection_date(self):
        """try to compute ps_inventory_inspection_date"""
        self.env['stock.picking'].search([('picking_id', '=', self.picking_id.id)]).write({'date_done': datetime.now()})
        record = self.env['stock.quant'].sudo().search([('lot_id', '=', self.lot_id),
                                                        ('location_id', '=', self.location_id)], limit=1)
        record._compute_inspection_date()

        with self.assertRaises(UserError):
            record.move_to_inventory_check_request()

    def test_inventory_check_request(self):
        """test the function inventory check request"""
        record = self.env['stock.quant'].sudo().search([('lot_id', '=', self.lot_id),
                                                        ('location_id', '=', self.location_id)], limit=1)
        with self.assertRaises(UserError):
            record.sudo(self.quality_user).move_to_inventory_check_request()
        # record.move_to_inventory_check_request()
        #
        # self.assertEqual(record.ps_is_request, True, 'Moving Failure')
        #
        # with self.assertRaises(UserError):
        #     record.move_to_inventory_check_request()
        #
        # check_request = self.env['ps.quality.inventory.check.request'].search([('lot_ids.lot_id', '=', self.lot_id),
        #                                                                        ('lot_ids.location_id', '=', self.location_id)], limit=1)
        # check_request.action_confirm()
        #
        # self.assertEqual(check_request.state, 'confirmed', 'Do not change state to confirmed')
        #
        # check_request.action_cancel()
        #
        # self.assertEqual(check_request.state, 'cancelled', 'Do not change state to cancel')
        #
        # check_request.action_draft()
        #
        # self.assertEqual(check_request.state, 'draft', 'Do not change state to draft')
        #
        # check_request.action_confirm()
        #
        # check_request.action_done()
        #
        # self.assertEqual(check_request.state, 'done', 'Do not change state to done')
