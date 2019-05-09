# -*- coding: utf-8 -*-
import logging

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
import datetime

_logger = logging.getLogger(__name__)


class TestCreditCheckScheme(TransactionCase):
    def setUp(self):
        super(TestCreditCheckScheme, self).setUp()

        self.user_manager = self.env['res.users'].create({
            'name': 'Loney Manager',
            'login': 'manager',
            'email': 'loney@example.com',
            'signature': '--\nAndreww',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('ps_credit_management.group_credit_officer').id, self.env.ref('base.group_user').id])]
        })

    def test_operate_state(self):
        object_credit_check_scheme_1 = self.env.ref('ps_credit_management.test_credit_check_scheme_id_1')
        object_credit_check_scheme_2 = self.env.ref('ps_credit_management.test_credit_check_scheme_id_2')
        object_credit_check_scheme_3 = self.env.ref('ps_credit_management.test_credit_check_scheme_id_3')

        object_credit_check_scheme_2.sudo(self.user_manager).draft()
        self.assertEqual(object_credit_check_scheme_2.state, "draft", "State not change")

        object_credit_check_scheme_2.sudo(self.user_manager).confirmed()
        self.assertEqual(object_credit_check_scheme_2.state, "confirmed", "State not change")

        object_credit_check_scheme_2.sudo(self.user_manager).cancelled()
        self.assertEqual(object_credit_check_scheme_2.state, "cancelled", "State not change")

        object_credit_check_scheme_2.sudo(self.user_manager).approved()
        self.assertEqual(object_credit_check_scheme_2.state, "approved", "State not change")
        self.assertEqual(object_credit_check_scheme_2.validate_date, datetime.date.today(), "validate_date not change")
        self.assertEqual(object_credit_check_scheme_2.validate_by.id, self.user_manager.id, "validate_by not change")

        object_credit_check_scheme_2.sudo(self.user_manager).closed()
        self.assertEqual(object_credit_check_scheme_2.is_default, False, "is_default not change")
        self.assertEqual(object_credit_check_scheme_2.state, "closed", "State not change")

        with self.assertRaises(UserError):
            object_credit_check_scheme_1.sudo(self.user_manager).closed()

        with self.assertRaises(UserError):
            object_credit_check_scheme_1.sudo(self.user_manager).unlink()

        object_credit_check_scheme_3.sudo(self.user_manager).unlink()

        object_credit_check_scheme_2.sudo(self.user_manager).copy_data()

    def test_constrains_func(self):
        with self.assertRaises(ValidationError):
            # 测试 name 重复
            self.env['ps.credit.check.scheme'].sudo(self.user_manager).create({
                'name': '测试检查规则1',
                'description': '该检查规则1用于测试 constrains方法',
                'is_default': False,
                'state': 'draft',
            })

        with self.assertRaises(ValidationError):
            # 测试 is_default 重复
            self.env['ps.credit.check.scheme'].sudo(self.user_manager).create({
                'name': '测试检查规则4',
                'description': '该检查规则4用于测试 constrains方法',
                'is_default': True,
                'state': 'draft',
            })

        with self.assertRaises(ValidationError):
            # 测试 document 重复
            self.env['ps.credit.check.rule'].sudo(self.user_manager).create({
                'document': 'sales_order',
                'control_strength': 'warning',
                'check_credit_limit': True,
                'check_credit_ratio': False,
                'check_overdue_days': False,
                'check_overdue_amount': False,
                'check_overdue_ratio': False,
                'excessive_condition': 'single',
                'scheme_id': self.env.ref('ps_credit_management.test_credit_check_scheme_id_1').id,
            })

    def test_copy_data(self):
        object_credit_check_scheme_1 = self.env.ref('ps_credit_management.test_credit_check_scheme_id_1')
        object_credit_check_scheme_1.copy_data()










