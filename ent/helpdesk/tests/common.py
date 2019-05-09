# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase


class HelpdeskTransactionCase(TransactionCase):

    def setUp(self):
        super(HelpdeskTransactionCase, self).setUp()

        # we create a helpdesk user and a manager
        self.main_company_id = self.env.ref('base.main_company').id
        self.helpdesk_manager = self.env['res.users'].create({
            'company_id': self.main_company_id,
            'name': 'Helpdesk Manager',
            'login': 'hm',
            'email': 'hm@example.com',
            'groups_id': [(6, 0, [self.env.ref('helpdesk.group_helpdesk_manager').id])]
        })
        self.helpdesk_user = self.env['res.users'].create({
            'company_id': self.main_company_id,
            'name': 'Helpdesk User',
            'login': 'hu',
            'email': 'hu@example.com',
            'groups_id': [(6, 0, [self.env.ref('helpdesk.group_helpdesk_user').id])]
        })
        # the manager defines a team for our tests (the .sudo() at the end is to avoid potential uid problems)
        self.test_team = self.env['helpdesk.team'].sudo(self.helpdesk_manager.id).create({'name': 'Test Team'}).sudo()
        # He then defines its stages
        stage_as_manager = self.env['helpdesk.stage'].sudo(self.helpdesk_manager.id)
        self.stage_new = stage_as_manager.create({
            'name': 'New',
            'sequence': 10,
            'team_ids': [(4, self.test_team.id, 0)],
            'is_close': False,
        }).sudo()
        self.stage_progress = stage_as_manager.create({
            'name': 'In Progress',
            'sequence': 20,
            'team_ids': [(4, self.test_team.id, 0)],
            'is_close': False,
        }).sudo()
        self.stage_done = stage_as_manager.create({
            'name': 'Done',
            'sequence': 30,
            'team_ids': [(4, self.test_team.id, 0)],
            'is_close': True,
        }).sudo()
        self.stage_cancel = stage_as_manager.create({
            'name': 'Cancelled',
            'sequence': 40,
            'team_ids': [(4, self.test_team.id, 0)],
            'is_close': True,
        }).sudo()

        # He also creates a ticket types for Question and Issue
        self.type_question = self.env['helpdesk.ticket.type'].sudo(self.helpdesk_manager.id).create({
            'name': 'Question_test',
        }).sudo()
        self.type_issue = self.env['helpdesk.ticket.type'].sudo(self.helpdesk_manager.id).create({
            'name': 'Issue_test',
        }).sudo()
