# -*- coding: utf-8 -*-
import logging

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestCreditProfile(TransactionCase):
    def setUp(self):
        super(TestCreditProfile, self).setUp()
        user = self.env['res.users'].with_context(no_reset_password=True)
        self.user_manager = user.create({
            'name': 'Andrew Manager',
            'login': 'manager',
            'email': 'a.m@example.com',
            'groups_id': [(6, 0, [self.env.ref('ps_credit_management.group_credit_officer').id])]
        })

        self.company_id = self.env.ref('base.main_company').id
        self.partner_id = self.env.ref('base.res_partner_category_0').id
        self.currency_id = self.env.ref('base.CNY').id
        self.level_id = self.env.ref("ps_credit_management.create_level_id").id
        self.check_scheme_id = self.env.ref('ps_credit_management.check_scheme_id').id

    def test_credit_profile(self):
        # test the approve and close button
        self.credit_profile = self.env['ps.credit.profile'].sudo(self.user_manager).search([('partner_id', '=', 7)])
        self.credit_profile.sudo(self.user_manager)._compute_date_end()
        self.credit_profile.sudo(self.user_manager).action_approve()

        self.assertEqual(self.credit_profile.sudo(self.user_manager).state, "confirmed", "State not change")

        self.credit_profile.sudo(self.user_manager).action_close()

        self.assertEqual(self.credit_profile.sudo(self.user_manager).state, "closed", "State not change")

        with self.assertRaises(UserError):
            self.credit_profile.sudo(self.user_manager).unlink()

    def test_date_start(self):
        # test date_start
        self.partner_id = self.env.ref('base.res_partner_category_2').id
        self.credit_profile = self.env['ps.credit.profile'].sudo(self.user_manager).search(
            [('partner_id', '=', 2)])
        self.credit_profile.sudo(self.user_manager)._compute_date_end()
        with self.assertRaises(UserError):
            self.credit_profile.assert_date_start()

    def test_unlink(self):
        # test unlink
        self.credit_profile = self.env['ps.credit.profile'].sudo(self.user_manager).search(
            [('partner_id', '=', 6)])

        self.credit_profile.sudo(self.user_manager)._compute_date_end()
        self.credit_profile.sudo(self.user_manager).unlink()

    def test_assert_less_than_zero(self):
        # Test whether the data is less than zero
        self.credit_profile = self.env['ps.credit.profile'].sudo(self.user_manager).search(
            [('partner_id', '=', 5)])
        with self.assertRaises(ValidationError):
            self.credit_profile.ratio = -1

        with self.assertRaises(ValidationError):
            self.credit_profile.credit_limit = -1

        with self.assertRaises(ValidationError):
            self.credit_profile.order_limit = -1

        with self.assertRaises(ValidationError):
            self.credit_profile.overdue_days = -1

        with self.assertRaises(ValidationError):
            self.credit_profile.overdue_limit = -1

        with self.assertRaises(ValidationError):
            self.credit_profile.overdue_ratio = -1

        with self.assertRaises(ValidationError):
            self.credit_profile.cycle_days = -1

    def test_is_repeat_date(self):
        # test date repeat
        self.credit_profile = self.env['ps.credit.profile'].sudo(self.user_manager).search(
            [('partner_id', '=', 4)])
        for profile in self.credit_profile:
            profile.action_approve()

        self.credit_profile = self.env['ps.credit.profile'].sudo(self.user_manager).search(
            [('partner_id', '=', 3)])
        self.credit_profile[0].action_approve()
        with self.assertRaises(UserError):
            self.credit_profile[1].action_approve()
