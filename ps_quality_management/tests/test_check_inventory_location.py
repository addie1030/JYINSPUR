# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestInventoryLocation(TransactionCase):
    def setUp(self):
        super(TestInventoryLocation, self).setUp()
        # user_group_adv = self.env.ref('stock.group_adv_location')
        # user_group_no_one = self.env.ref('base.group_no_one')
        # user_group_mul_warehouse = self.env.ref('stock.group_stock_multi_warehouses')
        # user_group_stock_manager = self.env.ref('stock.group_stock_manager')
        # # User Data: stock user
        # Users = self.env['res.users'].with_context({'no_reset_password': True, 'mail_create_nosubscribe': True})
        # self.user_stock_user = Users.create({
        #     'name': 'Pauline Poivraisselle',
        #     'login': 'pauline',
        #     'email': 'p.p@example.com',
        #     'notification_type': 'inbox',
        #     'groups_id': [(6, 0, [
        #         # user_group_adv.id,
        #         # user_group_no_one.id,
        #         # user_group_mul_warehouse.id,
        #         user_group_stock_manager.id,
        #     ])]
        # })
        self._warehouse = self.env['stock.warehouse'].sudo()

    def test_inspect_inventory(self):
        self._warehouse.create({
            'name': 'BEIJING',
            'code': 'BJ'
        })
        ps_inspect_wh_id = self._warehouse.search([('name','=', 'BEIJING')]).ps_inspect_wh_id
        self.assertEqual(ps_inspect_wh_id.name, 'inventory-qualitycheck', 'Init data is error.')
