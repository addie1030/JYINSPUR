# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestCreditUsage(TransactionCase):
    '''
    需要依据信用档案的预制数据测试信用状况查询
    demo数据：-i
        ps_credit_profile company_id 1 partner_id
    1. 信用档案插入数据  测试_get_profile_data
    2. 利用会计发票demo数据，测试_compute_posted_prepaid
    3. 测试预收款        _compute_prepaid
    4. 测试实际逾期额度  _compute_actual_overdue_limit
    5. 测试实际逾期比例   _compute_actual_overdue_ratio
    6. 测试实际逾期天数  _compute_actual_overdue_days
    7. 测试销售订单总金额  _compute_sale_order_amount
    8. 测试出库金额   _compute_outgoing_amount
    '''

    def setUp(self):
        super(TestCreditUsage, self).setUp()
        Users = self.env['res.users'].with_context(no_reset_password=True)
        self.user_manager = Users.create({
            'name': 'Andrew Manager',
            'login': 'manager',
            'email': 'a.m@example.com',
            'groups_id': [(6, 0, [self.env.ref('ps_credit_management.group_credit_officer').id,
                                  self.env.ref('account.group_account_invoice').id])]
        })
        self.account_id = self.env.ref('base.res_partner_1').property_account_receivable_id  # 应收账款的id account_id=211
        self.current_date = fields.Date.today()
        self.credit_profile = self.env['ps.credit.profile'].sudo(self.user_manager).search([])
        self.credit_usage = self.env['ps.credit.usage'].sudo(self.user_manager).search([])

    def test_credit_profile_data_confirmed(self):
        for record in self.credit_profile:
            if record.date_start <= self.current_date and self.current_date <= record.date_end:
                record.action_approve()
        self.credit_usage._get_profile_data()  # 获取信用档案的数据
        self.assertEqual(self.credit_usage.search([('partner_id', '=', 1)]).credit_ratio, 1.1,
                         'Credit Data is not same to credit profile.')

    # def test_credit_profile_data_closed(self):
    #     self.credit_profile.create({
    #         'company_id': self.env.ref('base.main_company'),
    #         'partner_id': self.env.ref('base.res_partner_category_0'),
    #         'currency_id': self.env.ref('base.CNY'),
    #         'level_id':self.env.ref('ps_credit_management.create_level_id'),
    #         'check_scheme_id':self.env.ref('ps_credit_management.check_scheme_id'),
    #         'date_start': self.current_date,
    #         'date_end': self.current_date + relativedelta(days=10),
    #         'state': 'closed',
    #         'ratio': 0.5,
    #         'credit_limit': 10000,
    #         'order_limit': 2000,
    #         'overdue_days': 5,
    #         'overdue_limit': 800,
    #         'overdue_ratio': 0.8,
    #     })
    #     print(self.credit_profile.search([('state','=', 'closed')]).partner_id.id)
    #     for record in self.credit_profile:
    #         record.action_close()
    #     self.credit_usage._get_profile_data()  # 获取信用档案的数据
    #     self.assertEqual(self.credit_usage.search([('partner_id', '=', 8)]).credit_ratio, 0,
    #                      'Credit Data is not same to credit profile.')
    #
    #     # else:
    #     #     print(record.id)
    #     #     record.action_close()
    #     #     self.credit_usage._get_profile_data()  # 获取信用档案的数据
    #     #     self.assertEqual(self.credit_usage.search([('partner_id', '=', 4)]).credit_ratio, 0,
    #     #                      'Credit Data is not same to credit profile.')
    #
    #     # self.assertEqual(self.credit_usage.credit_limit, 20000.0, 'Credit Data is not same to credit profile.')

    # def test_compute_posted_prepaid(self):
    #     self.credit_usage = self.env['ps.credit.usage'].sudo(self.user_manager).search(
    #         [('company_id', '=', self.company_id), ('partner_id', '=', 14)])
    #     posted_prepaid = self.credit_usage._compute_posted_prepaid(self.env.ref('base.res_partner_category_0'))
    #     print('************************')
    #     # print(self.partner_id)
    #     print(posted_prepaid)
    #     self.assertEqual(posted_prepaid, 0.0, '已过账的预付款')
    #     print('************************')

    # def test_compute_credit_data(self):
    #     self.credit_usage = self.env['ps.credit.usage'].sudo(self.user_manager).search(
    #         [('company_id', '=', self.company_id), ('partner_id', '=', 14)])
    #     print(self.credit_usage)
    #     self.credit_usage._compute_credit_data()
    #     self.assertEqual(self.credit_usage.used_limit, 0.0, '实际预期天数查询错误')
    #     self.assertEqual(self.credit_usage.actual_overdue_days, 0.0, '实际预期天数查询错误')
    #     self.assertEqual(self.credit_usage.actual_overdue_limit, 0.0, '实际预期天数查询错误')
    #     self.assertEqual(self.credit_usage.actual_overdue_ratio, 0.0, '实际预期天数查询错误')

    # def test_compute_prepaid(self):
    #     self.credit_usage = self.env['ps.credit.usage'].sudo(self.user_manager).search(
    #         [('company_id', '=', self.company_id), ('partner_id', '=', 14)])
    #     prepaid = self.credit_usage.sudo(self.user_manager)._compute_prepaid(self.account_id, self.profile_data)
    #     self.assertEqual(prepaid, 0.0, '预收账款错误')
