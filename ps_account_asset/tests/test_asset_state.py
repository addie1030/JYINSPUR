# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAssetState(TransactionCase):

    def setUp(self):
        # Useful models
        super(TestAssetState, self).setUp()
        self.AssetState = self.env['ps.asset.state']


    def tearDown(self):
        pass


    def test_asset_state(self):
        self.stateline = self.AssetState.create({
            'name': '状态1',
            'company_id': self.env.user.company_id.id,
            'describe':'测试资产状态',
            'is_depreciation': False,
            'active': True,
        })

        self.assertEqual(self.stateline.active, True, '资产状态无效')

        self.assertTrue(self.stateline.unlink(), 'Asset State is using, can not delete')


