# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date, time

from .common import HelpdeskTransactionCase
from odoo import fields


class TestHelpdeskSLA(HelpdeskTransactionCase):
    """ Test used to check that SLAs function as expected.
        - test_sla_base: tests the SLA gets applied and fails when it should
        - test_sla_priority: tests the correct SLA gets applied according to ticket priorities
        - test_sla_type: tests the correct SLA gets applied according to ticket types
    """

    def setUp(self):
        super(TestHelpdeskSLA, self).setUp()
        self.Sla = self.env['helpdesk.sla']
        # the manager enables our test team to use SLA's
        self.test_team.sudo(self.helpdesk_manager.id).write({'use_sla': True})
        # we check the associated group has correctly been applied to all users
        self.assertTrue(self.helpdesk_user.user_has_groups('helpdesk.group_use_sla'), "SLA group not applied to user after applying it to team.")
        # the manager then creates a SLA for our test team, to be applied to all its tickets regardless of type or priority
        self.test_sla = self.Sla.sudo(self.helpdesk_manager.id).create({
            'name': 'A day, an hour and a minute on all Tickets',
            'team_id': self.test_team.id,
            'stage_id': self.stage_done.id,
            'time_days': 1,
            'time_hours': 1,
        })

    def test_sla_base(self):
        # helpdesk user create a ticket
        ticket_creation_date = '2016-06-24 13:08:07'
        # counting from monday 1 day+ 1hour based on ticket creation time
        ticket_expected_deadline = '2016-06-27 14:08:07'

        ticket1 = self.env['helpdesk.ticket'].sudo(self.helpdesk_user.id).create({
            'name': 'test ticket 1',
            'team_id': self.test_team.id,
        })
        # we check the SLA is applied
        self.assertTrue(ticket1.sla_active and ticket1.sla_id == self.test_sla, "SLA didn't get associated to ticket.")
        # we rewind its creation date of more than the SLA time (we have to bypass the ORM as it doesn't let you write on create_date)
        ticket1._cr.execute(
            "UPDATE helpdesk_ticket set create_date=%s where id=%s",
            ["'" + ticket_creation_date + "'", ticket1.id])
        # invalidate the cache and manually run the compute as our cr.execute() bypassed the ORM
        ticket1.invalidate_cache()
        ticket1.sla_id = False  # the deadline will only be computed if the sla actually changes
        ticket1._compute_sla()
        ticket1.sla_id = self.test_sla
        ticket1._compute_sla()
        # helpdesk user closes the ticket
        ticket1.write({'stage_id': self.stage_done.id})
        # we verify the SLA is failed
        self.assertFalse(ticket1.sla_active)
        self.assertTrue(ticket1.sla_fail)
        self.assertEqual(str(ticket1.deadline), ticket_expected_deadline)

        # helpdesk user creates a second ticket and closes it without SLA fail
        ticket2 = self.env['helpdesk.ticket'].sudo(self.helpdesk_user.id).create({
            'name': 'test ticket 2',
            'team_id': self.test_team.id,
        })
        # helpdesk user closes the ticket
        ticket2.write({'stage_id': self.stage_done.id})
        # we check the sla didn't fail
        self.assertFalse(ticket2.sla_active)
        self.assertFalse(ticket2.sla_fail)

    def test_sla_priority(self):
        # the manager creates SLAs for ticket priorities
        self.test_sla_high = self.Sla.sudo(self.helpdesk_manager.id).create({
            'name': '20 hours on High Priority Tickets',
            'team_id': self.test_team.id,
            'stage_id': self.stage_done.id,
            'priority': '2',
            'time_hours': 20,
        })
        self.test_sla_urgent = self.Sla.sudo(self.helpdesk_manager.id).create({
            'name': '12 hours on Urgent Tickets',
            'team_id': self.test_team.id,
            'stage_id': self.stage_done.id,
            'priority': '3',
            'time_hours': 12,
        })
        # helpdesk user creates a ticket
        new_ticket = self.env['helpdesk.ticket'].sudo(self.helpdesk_user.id).create({
            'name': 'New Ticket',
            'team_id': self.test_team.id,
        })
        # we check the correct SLA is applied
        self.assertTrue(new_ticket.sla_id == self.test_sla, "Incorrect SLA associated with ticket.")
        # helpdesk user changes the priority of the ticket to high
        new_ticket.write({'priority': '2'})
        # we check the correct SLA is applied
        self.assertTrue(new_ticket.sla_id == self.test_sla_high, "Incorrect SLA associated with ticket.")
        # helpdesk user changes the priority of the ticket to urgent
        new_ticket.write({'priority': '3'})
        # we check the correct SLA is applied
        self.assertTrue(new_ticket.sla_id == self.test_sla_urgent, "Incorrect SLA associated with ticket.")

    def test_sla_type(self):
        # the manager creates SLAs for ticket types
        self.test_sla_question = self.Sla.sudo(self.helpdesk_manager.id).create({
            'name': '12 hours on Question Tickets',
            'team_id': self.test_team.id,
            'stage_id': self.stage_done.id,
            'ticket_type_id': self.type_question.id,
            'time_hours': 12,
        })
        self.test_sla_issue = self.Sla.sudo(self.helpdesk_manager.id).create({
            'name': '20 hours on Issue Tickets',
            'team_id': self.test_team.id,
            'stage_id': self.stage_done.id,
            'ticket_type_id': self.type_issue.id,
            'time_hours': 20,
        })
        # helpdesk user creates a ticket
        new_ticket = self.env['helpdesk.ticket'].sudo(self.helpdesk_user.id).create({
            'name': 'Undefined Ticket',
            'team_id': self.test_team.id,
        })
        # we check the correct SLA is applied
        self.assertTrue(new_ticket.sla_id == self.test_sla, "Incorrect SLA associated with ticket.")
        # helpdesk user changes the ticket type and we check the correct SLA is applied
        new_ticket.write({'name': 'Question Ticket', 'ticket_type_id': self.type_question.id})
        self.assertTrue(new_ticket.sla_id == self.test_sla_question, "Incorrect SLA associated with ticket.")

        # helpdesk user creates an issue ticket
        issue_ticket = self.env['helpdesk.ticket'].sudo(self.helpdesk_user.id).create({
            'name': 'Issue',
            'team_id': self.test_team.id,
            'ticket_type_id': self.type_issue.id,
        })
        # we check the correct sla is applied
        self.assertTrue(issue_ticket.sla_id == self.test_sla_issue, "Incorrect SLA associated with ticket.")
