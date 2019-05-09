# # -*- coding:utf-8 -*-
# import logging

from odoo.tests.common import TransactionCase


# _logger = logging.getLogger(__name__)
#
#
class TestQualitySamplingPlan(TransactionCase):
    def setUp(self):
        super(TestQualitySamplingPlan, self).setUp()

        self.plan_id = self.env.ref('ps_quality_management.inspection_plan')

    def test_action_confirm(self):
        self.plan_id.confirmed()
        self.assertEqual(self.plan_id.state, "confirmed", "Sampling Plan confirm failed")
