# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from datetime import datetime

class ReportTrialBalance(models.AbstractModel):
    _name = 'ps.account.dashboard'
    _description = 'ps.account.dashboard'

    # 取库存现金、银行存款科目当前余额、本期累计借方发生、本期累计贷方发生
    @api.model
    def get_account_amount(self):
        # 获取当前日期期间
        currentdate = datetime.today().strftime("%Y-%m-%d")
        period_ids = self.env['ps.account.period'].get_period(currentdate)
        if not period_ids:
            period_year = 0
            period_code = 0
        else:
            period_year = period_ids[0].year
            period_code = period_ids[0].period

        # 现金本期借方、本期贷方
        sql = """ select sum(account_move_line.debit),sum(account_move_line.credit) 
                          from account_account,account_move,account_move_line,ps_account_period
                          where account_move_line.account_id = account_account.id and account_move_line.move_id = account_move.id
                          and account_move.ps_period_code = ps_account_period.id and ps_account_period.year='%s' and ps_account_period.period='%s'"""% (period_year, period_code)
        self.env.cr.execute(sql)
        temp_ids1 = self.env.cr.fetchall()
        if temp_ids1[0][0] is not None:
            cash_debit_amount = temp_ids1[0][0]
        else:
            cash_debit_amount = 0
        if temp_ids1[0][1] is not None:
            cash_credit_amount = temp_ids1[0][1]
        else:
            cash_credit_amount = 0
        # 银行本期借方、本期贷方
        sql = """ select sum(account_move_line.debit),sum(account_move_line.credit) 
                                          from account_account,account_move,account_move_line,ps_account_period
                                          where account_move_line.account_id = account_account.id and account_move_line.move_id = account_move.id
                                          and account_move.ps_period_code = ps_account_period.id and ps_account_period.year='%s' and ps_account_period.period='%s'"""% (period_year, period_code)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()

        if temp_ids[0][0] is not None:
            bank_debit_amount = temp_ids[0][0]
        else:
            bank_debit_amount = 0
        if temp_ids[0][1] is not None:
            bank_credit_amount = temp_ids[0][1]
        else:
            bank_credit_amount = 0

        # 当前余额
        sql =""" select max(ps_account_period.period) from account_move LEFT JOIN ps_account_period ON account_move.ps_period_code = ps_account_period.id where name ='00000'  """
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        if temp_ids[0][0] is not None:
            max_period = temp_ids[0][0]
            # 现金
            sql=""" select (sum(account_move_line.debit) - sum(account_move_line.credit) ) from account_account,account_move,account_move_line,ps_account_period
	                    where account_move_line.account_id = account_account.id and account_move_line.move_id = account_move.id and account_move.ps_period_code = ps_account_period.id
	                    and ps_account_period.period > '%s' 
	                    and account_move_line.account_id = account_account.id 
	                     """ %(max_period)
            self.env.cr.execute(sql)
            temp_ids = self.env.cr.fetchall()
            if temp_ids[0][0] is not None:
                cash_amount = temp_ids[0][0]
            else:
                cash_amount = 0
            # 银行
            sql = """ select (sum(account_move_line.debit) - sum(account_move_line.credit) ) from account_account,account_move,account_move_line,ps_account_period
            	                    where account_move_line.account_id = account_account.id and account_move_line.move_id = account_move.id and account_move.ps_period_code = ps_account_period.id
            	                    and ps_account_period.period > '%s' 
            	                    and account_move_line.account_id = account_account.id 
            	                     """ % (max_period)
            self.env.cr.execute(sql)
            temp_ids = self.env.cr.fetchall()
            if temp_ids[0][0] is not None:
                bank_amount = temp_ids[0][0]
            else:
                bank_amount = 0
        else:
            # 现金
            sql="""select (sum(account_move_line.debit) - sum(account_move_line.credit) ) from account_account,account_move,account_move_line
	                    where account_move_line.account_id = account_account.id and account_move_line.move_id = account_move.id
	                    and account_move_line.account_id = account_account.id 
	                     """
            self.env.cr.execute(sql)
            temp_ids = self.env.cr.fetchall()
            if temp_ids[0][0] is not None:
                cash_amount = temp_ids[0][0]
            else:
                cash_amount = 0
            # 银行
            sql = """select (sum(account_move_line.debit) - sum(account_move_line.credit) ) from account_account,account_move,account_move_line
            	                    where account_move_line.account_id = account_account.id and account_move_line.move_id = account_move.id
            	                    and account_move_line.account_id = account_account.id 
            	                     """
            self.env.cr.execute(sql)
            temp_ids = self.env.cr.fetchall()
            if temp_ids[0][0] is not None:
                bank_amount = temp_ids[0][0]
            else:
                bank_amount = 0

        account_data = []
        account_data.append({
            'name': _('Cash in stock'),
            'totalamount': cash_amount,
            'debitamount': cash_debit_amount,
            'creditamount': cash_credit_amount,
        })
        account_data.append({
            'name': _('Cash in bank'),
            'totalamount': bank_amount,
            'debitamount': bank_debit_amount,
            'creditamount': bank_credit_amount,
        })
        return account_data

    # @api.model
    # def get_year_profit(self):
    #     # modules = self.env['ir.module.module'].search([('name', '=', 'account_statement')])
    #     # if not modules or modules.state == 'uninstalled':
    #     #     return[]
    #     profit_data = []
    #     profit_data.append(
    #         {
    #             'month': '01',
    #             'amount': 2500
    #         },
    #         {
    #             'month': '02',
    #             'amount': 4600
    #         },
    #         {
    #             'month': '03',
    #             'amount': 5800
    #         },
    #         {
    #             'month': '04',
    #             'amount': 2100
    #         },
    #         {
    #             'month': '05',
    #             'amount': 3300
    #         },
    #     )