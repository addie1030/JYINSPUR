# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields
import datetime
import logging
from dateutil.tz import gettz
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestPsAccountCarryOverCreate(TransactionCase):
    def setUp(self):
        super(TestPsAccountCarryOverCreate, self).setUp()
        self.get_amount_rule = self.env['ps.account.carry.over.amount']
        self.carry_over_move = self.env['ps.account.carry.over.move']
        self.carry_over_head = self.env['ps.account.carry.over.head']
        self.carry_over_create = self.env['ps.account.carry.over.create']
        self.period = self.env['ps.account.fiscalyear']
        period = self.period.create({
            'name': '2019',
            'date_start': '2019-01-01',
            'date_end': '2020-01-01',
        })
        period.create_period1()

    def create_amount_rule(self):
        """
        Create Get Voucher Amount Rules
        :return:
        """
        account_substr = 6  # 取科目编号前4位
        account_no = 101200  # 科目编号
        amount_ratio = 0.5  # 取数比例
        amount_range = 'DebitOccursY'  # 借方本年发生
        connector = '+'  # 取数为正数
        amount_rule = {
            'account_substr': account_substr,
            'account_no': account_no,
            'amount_ratio': amount_ratio,
            'amount_range': amount_range,
            'connector': connector,
        }
        return amount_rule

    def create_move_lines(self):
        """
        Create Carry Over Move Lines
        :return:
        """
        line_01 = self.carry_over_move.create({
            'account_id': 287,
            'balance_direction': 'debit',
            'partner_id': 1,
            'product_id': 1,
            'cashflow_id': 1,
            'amount_direction': 'plus'
        })
        line_01.rule_amount_ids = [(0, 0, self.create_amount_rule())]
        line_02 = self.carry_over_move.create({
            'account_id': 275,
            'balance_direction': 'credit',
            'partner_id': 1,
            'product_id': 1,
            'cashflow_id': 1,
            'amount_direction': 'plus',
            'take_other_total': True,
        })
        return line_01, line_02

    def create_carry_over_move(self):
        """
        Create Custom carry-over voucher head
        :return:
        """
        line_01, line_02 = self.create_move_lines()
        val = []
        ids = [line_01.id, line_02.id]
        val.append((6, 0, ids))
        self.carry_over_head.create({
            'carry_over_move_no': 'Test001',
            'name': 'Test001',
            'move_ids': val,
            'is_generate': True,
        })

    def test_create_carry_over_move(self):
        """
        Create Custom carry-over voucher
        :return:
        """
        self.create_carry_over_move()
        carry_over_create = self.carry_over_create.create({
            'journal_id': 78,
        })
        carry_over_create_id = carry_over_create.id
        carry_over_create.post()  # 生成自定义结转凭证
        move = self.env['account.move'].search([('carry_over_head_id', '!=', False)])
        self.assertTrue(move, '未生成自定义结转凭证')



