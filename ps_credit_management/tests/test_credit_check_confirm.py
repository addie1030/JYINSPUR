# -*- coding: utf-8 -*-
import logging

from odoo.tests.common import TransactionCase
from addons.sale.tests.test_sale_order import TestSaleOrder
from addons.stock.tests.test_move import StockMove

_logger = logging.getLogger(__name__)


class TestCheckConfirm(TestSaleOrder):
    @classmethod
    def setUpClass(cls):
        super(TestCheckConfirm, cls).setUpClass()
        SaleCreditWizard = cls.env['ps.credit.confirm.wizard']
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.user_manager = Users.create({
            'name': 'Andrew Manager',
            'login': 'manager',
            'email': 'a.m@example.com',
            'groups_id': [(6, 0, [cls.env.ref('ps_credit_management.group_credit_officer').id,
                                  cls.env.ref('account.group_account_invoice').id])]
        })
        cls.sale_credit_wizard = SaleCreditWizard.create({
            'order': cls.sale_order.id,
        })
        cls.sale_order_1 = cls.env.ref('sale.sale_order_1')
        cls.sale_order_2 = cls.env.ref('sale.sale_order_2')

    def test_credit_profile(self):
        self.sale_credit_wizard.continue_sale()
        self.assertTrue(self.sale_order.state == 'sale', "Continue sale not working")

    def test_order_check(self):
        msg_1 = self.sale_order_1.check_sale_order()
        logging.info('_______________________msg:%s', msg_1)
        self.sale_order_1.action_confirm()
        self.assertTrue(msg_1, 'Sale order credit check error')
        self.assertFalse(self.sale_order_1.state == 'sale',
                         'Sale order credit check error:check not pass but sale order confirmed')

        msg_2 = self.sale_order_2.check_sale_order()
        self.sale_order_1.action_confirm()
        self.assertFalse(msg_2, 'Sale order credit check error')
        self.assertTrue(self.sale_order_2.state == 'sale',
                        'Sale order credit check error:check pass but sale order confirm failed')

    def test_check_order(self):
        self.sale_order1 = self.env.ref('ps_credit_management.test_sale_order_demo')
        msg1=self.sale_order1.check_sale_order()
        self.sale_order1.action_confirm()
        self.assertTrue(msg1,'Sale order check error')
        self.assertTrue(self.sale_order.state != 'sale','Check sale order not pass: error(order confirmed)')

        self.sale_order2 = self.env.ref('ps_credit_management.test_sale_order_demo1')
        msg2 = self.sale_order2.check_sale_order()
        self.sale_order2.action_confirm()
        self.assertFalse(msg2, 'Sale order check error')
        self.assertTrue(self.sale_order.state == 'sale', 'Check sale order pass: error(order confirmed failed)')

        continue_sale = self.env.context.set('continue_sale', False)
        msg3 = self.sale_order1.check_sale_order()
        self.sale_order1.action_confirm()
        self.assertFalse(msg3, 'Sale order check error')
        self.assertTrue(self.sale_order.state == 'sale', 'Check sale order pass: error(order confirmed failed)')


class TestStockValidate(StockMove):
    def test_stock_validate(self):
        StockPickingWizard = self.env['ps.credit.confirm.stock.wizard']
        partner = self.env['res.partner'].create({'name': 'Jean'})
        self.picking = self.env['stock.picking'].create({
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'partner_id': partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
        })
        self.stock_picking_wizard = StockPickingWizard.create({
            'pick_id': self.picking.id
        })
        self.stock_picking_wizard.continue_move()
        self.assertTrue(self.picking.state == 'done', "Continue stock picking not working")
