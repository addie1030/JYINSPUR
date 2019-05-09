# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo.fields import Datetime
from odoo.tools import mute_logger

from odoo.addons.test_marketing_automation.tests.common import MarketingCampaignTestBase


class MarketingCampaignTest(MarketingCampaignTestBase):

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.models')
    def test_simple_flow(self):
        date = Datetime.from_string('2014-08-01 15:02:32')  # so long, little task
        self.mock_datetime.now.return_value = date
        self.mock_datetime2.now.return_value = date

        Campaign = self.env['marketing.campaign'].sudo(self.user_market)
        Activity = self.env['marketing.activity'].sudo(self.user_market)
        MassMail = self.env['mail.mass_mailing'].sudo(self.user_market)
        ServerAction = self.env['ir.actions.server'].sudo(self.user_market)

        # Create campaign
        campaign = Campaign.create({
            'name': 'My First Campaign',
            'model_id': self.test_model.id,
            'domain': '%s' % ([('name', '!=', 'Invalid')]),
        })

        # Create first activity flow
        mass_mailing = MassMail.create({
            'name': 'Hello',
            'body_html': '<div>My Email Body</div>',
            'mailing_model_id': self.test_model.id,
            'use_in_marketing_automation': True,
        })
        act_0 = Activity.create({
            'name': 'Enter the campaign',
            'campaign_id': campaign.id,
            'activity_type': 'email',
            'mass_mailing_id': mass_mailing.id,
            'trigger_type': 'begin',
            'interval_number': '0',
        })

        # NOTSURE: let us consider currently that a smart admin created the server action for the marketing user, is probably the case actually
        server_action = ServerAction.sudo().create({
            'name': 'Update name',
            'state': 'code',
            'model_id': self.test_model.id,
            'code': '''
for record in records:
    record.write({'name': record.name + 'SA'})'''
        })
        act_1 = Activity.create({
            'name': 'Update name',
            'domain': '%s' % ([('name', 'ilike', 'Test')]),
            'campaign_id': campaign.id,
            'parent_id': act_0.id,
            'activity_type': 'action',
            'server_action_id': server_action.sudo(self.user_market).id,
            'trigger_type': 'act',
            'interval_number': '1',
            'interval_type': 'hours',
        })

        # User starts and syncs its campaign
        campaign.action_start_campaign()
        self.assertEqual(campaign.state, 'running')
        campaign.sync_participants()

        # All records not containing Invalid should be added as participants
        self.assertEqual(campaign.running_participant_count, 4)
        self.assertEqual(
            set(campaign.participant_ids.mapped('res_id')),
            set((self.test_rec1 | self.test_rec2 | self.test_rec3 | self.test_rec4).ids)
        )
        self.assertEqual(set(campaign.participant_ids.mapped('state')), set(['running']))

        # Begin activity should contain a trace for each participant
        self.assertEqual(
            act_0.trace_ids.mapped('participant_id'),
            campaign.participant_ids,
        )
        self.assertEqual(set(act_0.trace_ids.mapped('state')), set(['scheduled']))
        self.assertEqual(set(act_0.trace_ids.mapped('schedule_date')), set([date]))

        # No other trace should have been created as the first one are waiting to be processed
        self.assertEqual(act_1.trace_ids, self.env['marketing.trace'])

        # First traces are processed, emails are sent
        campaign.execute_activities()
        self.assertEqual(set(act_0.trace_ids.mapped('state')), set(['processed']))

        # Child traces should have been generated for all traces of parent activity as filter is taken into account at processing, not generation
        self.assertEqual(
            set(act_1.trace_ids.mapped('participant_id.res_id')),
            set((self.test_rec1 | self.test_rec2 | self.test_rec3 | self.test_rec4).ids)
        )
        self.assertEqual(set(act_1.trace_ids.mapped('state')), set(['scheduled']))
        self.assertEqual(set(act_1.trace_ids.mapped('schedule_date')), set([date + relativedelta(hours=1)]))

        # Traces are processed, but this is not the time to execute child traces
        campaign.execute_activities()
        self.assertEqual(set(act_1.trace_ids.mapped('state')), set(['scheduled']))

        # Time is coming, a bit like the winter
        date = Datetime.from_string('2014-08-01 17:02:32')  # wow, a two hour span ! so much incredible !
        self.mock_datetime.now.return_value = date
        self.mock_datetime2.now.return_value = date

        campaign.execute_activities()
        # There should be one rejected activity not matching the filter
        self.assertEqual(
            set(act_1.trace_ids.filtered(lambda tr: tr.participant_id.res_id != self.test_rec4.id).mapped('state')),
            set(['processed'])
        )
        self.assertEqual(
            set(act_1.trace_ids.filtered(lambda tr: tr.participant_id.res_id == self.test_rec4.id).mapped('state')),
            set(['rejected'])
        )
        # Check server action was actually processed
        self.assertTrue([
            'SA' in record.name
            for record in self.test_rec1 | self.test_rec2 | self.test_rec3])
        self.assertTrue([
            'SA' not in record.name
            for record in self.test_rec4])

    @mute_logger('odoo.addons.base.ir.ir_model', 'odoo.models')
    def test_missing_record(self):
        Campaign = self.env['marketing.campaign'].sudo(self.user_market)
        Activity = self.env['marketing.activity'].sudo(self.user_market)
        MassMail = self.env['mail.mass_mailing'].sudo(self.user_market)

        name_field = self.env['ir.model.fields'].search(
            [('model_id', '=', self.test_model.id), ('name', '=', 'display_name')])

        campaign = Campaign.create({
            'name': 'My First Campaign',
            'model_id': self.test_model.id,
            'domain': '%s' % ([('name', '!=', 'Invalid')]),
        })

        mass_mailing = MassMail.create({
            'name': 'Hello',
            'body_html': '<div>My Email Body</div>',
            'mailing_model_id': self.test_model.id,
            'use_in_marketing_automation': True,
        })
        act_0 = Activity.create({
            'name': 'Enter the campaign',
            'campaign_id': campaign.id,
            'activity_type': 'email',
            'mass_mailing_id': mass_mailing.id,
            'trigger_type': 'begin',
            'interval_number': '0',
        })

        campaign.action_start_campaign()
        self.assertEqual(campaign.state, 'running')
        campaign.sync_participants()

        first_recordset = self.test_rec1 | self.test_rec2 | self.test_rec3 | self.test_rec4

        self.assertEqual(campaign.running_participant_count, 4)
        self.assertEqual(
            set(campaign.participant_ids.mapped('res_id')),
            set(first_recordset.ids)
        )

        self.test_rec1.unlink()
        campaign.sync_participants()

        # the missing record should have been removed (and not caused any crash)
        self.assertEqual(campaign.running_participant_count, 3)
        # note that the participant itself is not removed, only its state is modified (from running to unlinked)
        self.assertEqual(
            set(campaign.participant_ids.mapped('res_id')),
            set(first_recordset.ids)
        )
