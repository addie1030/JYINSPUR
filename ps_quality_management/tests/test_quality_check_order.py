# # -*- coding:utf-8 -*-
# import logging

from odoo.tests.common import TransactionCase


# _logger = logging.getLogger(__name__)
#
#
class TestQualityCheckOrder(TransactionCase):
    def setUp(self):
        super(TestQualityCheckOrder, self).setUp()

        self.plan_id = self.env.ref('ps_quality_management.inspection_plan')
        self.plan_templ_id = self.env.ref('ps_quality_management.inspection_plan_templ')
        self.picking_id = self.env.ref('ps_quality_management.inspection_plan')

    def write_product_templ(self):
        product_id = self.ref('product_product_computer')
        self.plan_id.product_tmpl_id = product_id.product_tmpl_id.id

        for line in self.plan_id.inspection_plan_testing_item_ids:
            line.product_tmpl_id = product_id.product_tmpl_id.id
            line.product_id = product_id.id

        self.plan_templ_id.product_variant_id = product_id.id
        self.plan_templ_id.product_tmpl_id = product_id.product_tmpl_id.id

        for line in self.plan_templ_id.inspection_plan_testing_item_ids:
            line.product_tmpl_id = product_id.product_tmpl_id.id
            line.product_id = product_id.id

    def move_action_confirm(self):
        self.picking_id.action_confrim()

    def test_crate_check(self):
        self.write_product_templ()
        self.picking_id.move_action_confrim()
