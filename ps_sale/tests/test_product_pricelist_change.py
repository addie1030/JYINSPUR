# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
import datetime
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestProductPricelistChange(TransactionCase):
    def setUp(self):
        super(TestProductPricelistChange, self).setUp()
        self.user_manager = self.env['res.users'].create({
            'name': 'Loney Manager',
            'login': 'manager',
            'email': 'loney@example.com',
            'signature': '--\nAndreww',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('ps_sale.group_price_change_user').id, self.env.ref('sales_team.group_sale_manager').id])]
        })

    def test_operate_state(self):
        # self.env('ps_sale.ps.product.pricelist.change').create()

        object_product_pricelist_change_demo_1 = self.env.ref('ps_sale.test_product_pricelist_change_demo_1')

        object_product_pricelist_change_demo_1.sudo(self.user_manager).submit()
        self.assertEqual(object_product_pricelist_change_demo_1.state, "confirmed", "State not change")

        object_product_pricelist_change_demo_1.sudo(self.user_manager).cancer()
        self.assertEqual(object_product_pricelist_change_demo_1.state, "cancer", "State not change")

        object_product_pricelist_change_demo_1.sudo(self.user_manager).close()
        self.assertEqual(object_product_pricelist_change_demo_1.state, "close", "State not change")

        object_product_pricelist_change_demo_1.sudo(self.user_manager).load_price_detail()

        with self.assertRaises(UserError):
            object_product_pricelist_change_demo_1.sudo(self.user_manager).unlink()

        object_product_pricelist_change_demo_1.sudo(self.user_manager).draft()
        self.assertEqual(object_product_pricelist_change_demo_1.state, "draft", "State not change")

        object_product_pricelist_change_demo_1.sudo(self.user_manager).unlink()

        self.env['ps.product.pricelist.change'].sudo(self.user_manager).create({
            'description': 'this is a test product pricelist change',
        })

        object_product_pricelist_change_line_demo_1 = self.env['ps.product.pricelist.change.line'].sudo(self.user_manager).create({
            'lines_id': self.env.ref('ps_sale.test_product_pricelist_change_demo_1'),
            'price_old': -1,
            'price_new': -1,
            'min_qty_old': -1,
            'min_qty_new': -1,
            'start_date_new': '2019-02-01',
            'end_date_new': '2019-01-01',
        })

        object_product_pricelist_change_demo_1.sudo(self.user_manager).review()

        with self.assertRaises(UserError):
            object_product_pricelist_change_line_demo_1._onchange_price_new()

        object_product_pricelist_change_line_demo_1._onchange_price_factor()

        with self.assertRaises(UserError):
            object_product_pricelist_change_line_demo_1._onchange_min_qty_new()

        with self.assertRaises(UserError):
            object_product_pricelist_change_line_demo_1._onchange_date()

        object_product_pricelist_change_line_demo_1.sudo(self.user_manager).write({
            'method': 'percentage',
            'price_old': 10,
            'factor': 1,
        })
        object_product_pricelist_change_line_demo_1._onchange_price_new()
        object_product_pricelist_change_line_demo_1._onchange_price_factor()

        object_product_pricelist_change_line_demo_2 = self.env['ps.product.pricelist.change.line'].sudo(
            self.user_manager).create({
            'price_old': 1,
            'price_new': -1,
            'min_qty_old': 2,
            'min_qty_new': 2,
            'start_date_old': '2019-02-01',
            'end_date_new': '2019-01-01',
        })
        with self.assertRaises(UserError):
            object_product_pricelist_change_line_demo_2._onchange_price_factor()

        with self.assertRaises(UserError):
            object_product_pricelist_change_line_demo_2._onchange_date()

        object_product_pricelist_change_line_demo_2.sudo(self.user_manager).write({
            'end_date_old': '2019-01-01',
            'start_date_new': '2019-02-01',
            'end_date_new': None,
        })
        with self.assertRaises(UserError):
            object_product_pricelist_change_line_demo_2._onchange_date()