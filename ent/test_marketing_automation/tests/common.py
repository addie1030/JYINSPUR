# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from odoo.fields import Datetime
from odoo.tests import common


class MarketingCampaignTestBase(common.TransactionCase):

    def setUp(self):
        super(MarketingCampaignTestBase, self).setUp()

        Users = self.env['res.users'].with_context(no_reset_password=True)
        self.user_market = Users.create({
            'name': 'Juliette MarketUser',
            'login': 'juliette',
            'email': 'juliette.marketuser@example.com',
            'groups_id': [(6, 0, [self.ref('base.group_user'), self.ref('marketing_automation.group_marketing_automation_user')])]
        })

        self.test_model = self.env.ref('test_mail.model_mail_test_simple')
        TestModel = self.env['mail.test.simple']
        self.test_rec0 = TestModel.create({'name': 'Invalid'})
        self.test_rec1 = TestModel.create({'name': 'Test_1'})
        self.test_rec2 = TestModel.create({'name': 'Test_2'})
        self.test_rec3 = TestModel.create({'name': 'Test_3'})
        self.test_rec4 = TestModel.create({'name': 'Brol_1'})

        self.patcher = patch('odoo.addons.marketing_automation.models.marketing_campaign.Datetime', wraps=Datetime)
        self.patcher2 = patch('odoo.addons.marketing_automation.models.marketing_participant.Datetime', wraps=Datetime)
        
        self.mock_datetime = self.patcher.start()
        self.mock_datetime2 = self.patcher2.start()

    def tearDown(self):
        self.patcher.stop()
        super(MarketingCampaignTestBase, self).tearDown()
