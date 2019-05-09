# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestCheckInventoryDate(TransactionCase):
    def setUp(self):
        super(TestCheckInventoryDate, self).setUp()
        self.stock_product_lot = self.env['stock.production.lot']

    def test_check_inventory_date(self):
        pass