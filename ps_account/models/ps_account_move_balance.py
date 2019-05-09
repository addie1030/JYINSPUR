# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import api,  models, fields, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import datetime

############################################
# describe：余额初始、期末结转（损益结转）、期末结账
# date：20180528
# author：sunny
############################################

class PsAccountMoveBalance(models.Model):
    _inherit = 'account.move'

    @api.onchange('line_ids')
    def opening_move_line_ids_changed(self):
        # if self.id != self.company_id.account_opening_move_id.id:
        #     return None
        self.ensure_one()
        if not self.env.context.get('id',False):
            return
        # self.id取不到值，顾此处通过context获取
        if self.env.context.get('id') != self.company_id.account_opening_move_id.id:
            return

        debit_diff, credit_diff = self.company_id.get_opening_move_differences(self.line_ids)

        unaffected_earnings_account = self.company_id.get_unaffected_earnings_account()
        balancing_line = self.line_ids.filtered(lambda x: x.account_id == unaffected_earnings_account)

        if balancing_line:
            if not self.line_ids == balancing_line and (debit_diff or credit_diff):
                balancing_line.debit = credit_diff
                balancing_line.credit = debit_diff
            else:
                self.line_ids -= balancing_line
        elif debit_diff or credit_diff:

            balancing_line = self.env['account.move.line'].new({
                'name': '',
                'move_id': self.company_id.account_opening_move_id.id,
                'account_id': unaffected_earnings_account.id,
                'debit': credit_diff,
                'credit': debit_diff,
                'company_id': self.company_id.id,
            })
            self.line_ids += balancing_line

    # 科目余额初始
    # 系统初次使用时，分录需要手工录入或外部文件导入，年结时根据计算结果自动生成一张余额初始凭证
    @api.model
    def setting_opening_move_action(self):
        """ Called by the 'Initial Balances' button of the setup bar."""
        company = self.env.user.company_id

        # If the opening move has already been posted, we open its form view
        if not company.account_opening_move_id.id:
            if not company.account_opening_move_id:
                default_journal = self.env['account.journal'].search(
                    [('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)

                if not default_journal:
                    raise UserError(_("No miscellaneous journal could be found. Please create one before proceeding."))

                company.account_opening_move_id = self.env['account.move'].create({
                    'name': _('opening move'),
                    'company_id': company.id,
                    'journal_id': default_journal.id,
                })

        form_view_id = self.env.ref('ps_account.view_move_form_new').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('opening move'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'target': 'current',
            'res_id': company.account_opening_move_id.id,
            'views': [[form_view_id, 'form']],
            'context': {'view_no_maturity': 1,'id': company.account_opening_move_id.id},
        }

    # 损益结转：统计自当前会计区间至现在的损益类科目的余额，根据科目的余额方向生成凭证
    @api.model
    def create_profit_loss_move(self, cur_kjqj):
        if len(cur_kjqj) == 6:
            kjqj_year = cur_kjqj[0:4]
            kjqj_month = cur_kjqj[4:]
        else:
            raise ValidationError(_('Can not get the accounting period, please maintain.'))

        period_ids = self.env['ps.account.period'].search(
            [('year', '=', kjqj_year), ('period', '=', kjqj_month), ('company_id', '=', self.env.user.company_id.id)])
        if period_ids:
            for r in period_ids:
                res = self.search([('ps_period_code', '=', r.id),
                                   ('ref', '=', _('Profit and loss transfer certificate'))], limit=1)
                if res:
                    account_move_id = res.id
                else:
                    if period_ids[0].financial_state == '2':
                        raise ValidationError(_('This period has been settled and cannot be carried forward!'))
                    billdate = period_ids[0].date_end
                    # 检查当前会计年度
                    current_kjqj= self.env.user.company_id.ps_current_fiscalyear
                    if not current_kjqj:
                        raise UserError(_("There is no activation period yet, please enable it in the accounting period function!"))
                    automatic_post = self.env.user.company_id.ps_profit_loss_same_user_approval   #损益结转生成的凭证是否自动审核记账

                    # 检查账簿类型
                    default_journal = self.env['account.journal'].search([('type', '=', 'general'),
                                                                          ('company_id', '=', self.env.user.company_id.id)],
                                                                         limit=1)
                    if not default_journal:
                        raise UserError(_("Please create a generic book type first!"))
                    # 检查损益结转科目是否定义
                    profit_account_id = self.env.user.company_id.ps_account_profit_id.id
                    if not profit_account_id:
                        raise UserError(_("Please set the subject to be carried over first!"))
                    res_account = self.env['account.account'].search([('id', '=', profit_account_id)], limit=1)
                    if res_account and res_account.ps_auxiliary_state == '1':
                        raise UserError(_("The carried over subject has auxiliary accounting and cannot complete the automatic carry-over!"))

                    new_account_move_data = {
                        'name': _('Profit and loss transfer certificate'),
                        'company_id': self.env.user.company_id.id,
                        'journal_id': default_journal.id,
                        # 'ps_period_year': kjqj_year,
                        # 'ps_period_code': kjqj_month,
                        'date': billdate,
                    }
                    if automatic_post:
                        new_account_move_data.update({
                            'state': 'posted',
                            'ps_confirmed_user': self.env.user.id,
                            'ps_confirmed_datetime': datetime.date.today(),
                            'ps_posted_user': self.env.user.id,
                            'ps_posted_datetime': datetime.date.today(),
                        })

                    # 计算损益类科目，根据科目的余额方向处理，需要考虑辅助核算：
                    # 1、余额方向在借方：将月结月份以后的该科目的 “借方合计 - 贷方合计” 放到结转凭证的贷方
                    # 2、余额方向在贷方：将月结月份以后的该科目的 “借方合计 - 贷方合计” 放到结转凭证的借方
                    # 选取内容：0余额方向、1科目编码、2科目id、3余额、4外币余额、5数量余额，6币种、7产品、8计量单位、9往来单位、10员工、11部门、12专项1、13专项2...
                    # 取损益类科目属性的id
                    profit_loss_attribute_id = self.env.user.company_id.profit_loss_attribute_id
                    if not profit_loss_attribute_id:
                        profit_loss_attribute_id = '5'  # 此参数的值和科目一起预置，正常情况下用不到
                    sql = """select account.ps_balance_direction as direction,account.code, mx.account_id,sum(balance) as balance, 
                                             sum(amount_currency) as currency_balance,sum(quantity) as quantity_balance,mx.currency_id,
                                             mx.product_id,mx.product_uom_id,mx.partner_id
                                             from account_move_line mx 
                                             left join account_move hz on mx.move_id=hz.id 
                                             left join account_account account on mx.account_id=account.id 
                                             left join ps_account_period d ON hz.ps_period_code = d.id
                                             where account.account_attribute_id=%s and d.year>='%s' and d.period>='%s' 
                                             and  d.year<='%s' and d.period<='%s'
                                             group by mx.account_id,account.code,account.ps_balance_direction,mx.currency_id,
                                             mx.product_id,mx.product_uom_id,mx.partner_id
                                             having sum(balance)!=0 """ % (int(profit_loss_attribute_id), kjqj_year, kjqj_month,
                                                                           period_ids[0].year, period_ids[0].period)
                    self.env.cr.execute(sql)
                    line_ids = self.env.cr.fetchall()

                    debit_total = 0
                    credit_total = 0
                    new_line_ids_data = []

                    if not line_ids:
                        raise UserError(_("There are no subjects that need to be carried over!"))
                    for record in line_ids:
                        # 根据余额方向判断放在贷方还是借方，余额在借方，差额填入贷方
                        if record[0] == '1':
                            debit1 = 0
                            credit1 = record[3]
                            balance1 = - record[3]
                            credit_total += record[3]

                            # debit_currency = 0
                            # credit_currency = record[4]
                            amount_currency = - record[4]

                            # debit_quantity = 0
                            # credit_quantity = record[5]
                            quantity = - record[5]

                        else:
                            debit1 = - record[3]
                            credit1 = 0
                            balance1 = - record[3]
                            debit_total += - record[3]

                            # debit_currency = - record[4]
                            # credit_currency = 0
                            amount_currency = - record[4]

                            # debit_quantity = - record[5]
                            # credit_quantity = 0
                            quantity = - record[5]

                        new_line_ids_data.append((0, 0, {
                            'name': _('Profit and loss carryover'),
                            'company_id': self.env.user.company_id.id,
                            'journal_id': default_journal.id,
                            'account_id': record[2],
                            'debit': debit1,
                            'credit': credit1,
                            'balance': balance1,

                            # 'debit_currency': debit_currency,
                            # 'credit_currency': credit_currency,
                            'amount_currency': amount_currency,

                            # 'debit_quantity': debit_quantity,
                            # 'credit_quantity': credit_quantity,
                            'quantity': quantity,
                            'ref':  _('Profit and loss transfer certificate'),

                            'currency_id': record[6],
                            'product_id': record[7],
                            'product_uom_id': record[8],
                            'partner_id': record[9],
                        }))

                        # 增加本年利润分录
                    if credit_total != debit_total:
                        if abs(debit_total) > abs(credit_total):
                            debit1 = 0
                            credit1 = debit_total - credit_total
                            balance1 = -(debit_total - credit_total)
                        else:
                            debit1 = -(debit_total - credit_total)
                            credit1 = 0
                            balance1 = -(debit_total - credit_total)

                        new_line_ids_data.append((0, 0, {
                            'name': _('Profit and loss carryover'),
                            'company_id': self.env.user.company_id.id,
                            'journal_id': default_journal.id,
                            'account_id': int(profit_account_id),
                            'debit': debit1,
                            'credit': credit1,
                            'balance': balance1,
                            'ref':  _('Profit and loss transfer certificate'),
                        }))
                        new_account_move_data['line_ids'] = new_line_ids_data
                        new_account_move = self.env['account.move'].with_context(
                            {'check_move_validity': False, 'background_code_generate': '1'}).create(new_account_move_data)

                        account_move_id = new_account_move.id

        form_view_id = self.env.ref('ps_account.view_move_form_new').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Profit and loss transfer certificate'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'target': 'current',
            'res_id': account_move_id,
            'views': [[form_view_id, 'form']],
            'context': {'search_default_misc_filter': 1, 'view_no_maturity': 1, 'id': account_move_id, 'manual_move': '1'},
        }


    # 结账前提：
    # 检查1）
    #     未月结的期间可以结账，不能跨越结账，如02区间未月结，就不能月结03区间
    #     如果月结时的日期未到区间的结束日期，给出提示“月结后，本区间将不能做凭证，是否继续？”
    # 检查2）
    #     检查要月结区间的所有凭证都已记账且未作废（不能有未作废且有未记账的凭证）
    #     判断资产类科目是否有赤字（库存现金、银行存款）
    #     判断损益类科目是否已结转，有余额的提示未结转
    #     凭证断号检查，不允许有空号，只给出提示，不用系统处理
    # 处理1）
    #     修改此会计区间的财务状态为“月结”（ps_account_period表的financial_state值为1）
    #     修改月结期间ps_account_config表中的key =“cw_kjqj”的值为刚月结的年度加期间（如果没有这条记录则插入，note =“最后月结的年度和区间”）
    #       如果当前会计区间是最后一个区间时，自动年结
    # 处理2）
    #     科目表(account_account)根据当前会计年度生成下一年度的科目（只修改年度后插入）
    #     自动建一张初始凭证，凭证的分录是 （前一年的明细科目余额 <> 0的科目）（查询的时候，年度 >= 当前会计年度），并将此凭证关联到公司上
    #     检查会计年度表（ps_account_fiscalyear）中是否有下一会计年度的数据，如果没有则以当前会计年度的数据形成下一会计年度的数据
    #       （会计年度 + 1，各期间的开始结束日期年份加1，要注意2月的日期），并默认启用；
    #     修改此会计区间的财务状态为“月结”（ps_account_period表的financial_state值为1）
    #     修改会计年度表（ps_account_fiscalyear）中当前会计年度的状态为“已年结”
    #     修改配置表（ps_account_config）中键为“cw_kjqj”的值为下一会计年度 + 第一个会计期间
    def _ps_period_month_end(self, cur_year, cur_period):
        #     修改此会计区间的财务状态为“月结”（ps_account_period表的financial_state值为1）
        #     修改月结期间ps_account_config表中的key =“cw_kjqj”的值为刚月结的年度加期间（如果没有这条记录则插入，note =“最后月结的年度和区间”）
        self.env['ps.account.period'].search([('year', '=', cur_year), ('period', '=', cur_period)]).write({'financial_state': '2'})

        period_ids = self.env['ps.account.period'].search([('year', '=', cur_year), ('period', '>', cur_period)])
        if period_ids:
            period = str(int(cur_period) + 1).zfill(2)
            new_cw_kjqj = cur_year + period
            #更新当前会计期间
            self.env.user.company_id.write({'ps_current_fiscalyear': new_cw_kjqj})
            self.env['ps.account.period'].search([('year', '=', cur_year), ('period', '=', period),
                                                  ('company_id', '=', self.env.user.company_id.id)]).write({'financial_state': '1'})
        else:
            new_cw_kjqj = str(int(cur_year) + 1) + '01'
            #更新当前会计期间
            self.env.user.company_id.write({'ps_current_fiscalyear': new_cw_kjqj})
            self._ps_period_year_end(cur_year, cur_period)
        return True

    def _ps_period_year_end(self, cur_year, cur_period):
        # 1、新一年会计期间
        fiscalyear_record = self.env['ps.account.fiscalyear'].search([('name', '=', cur_year)], limit=1)
        fiscalyear_record.write({'state': '2'})

        newyear = str(int(fiscalyear_record.name) + 1)
        newfiscalyear = self.env['ps.account.fiscalyear'].search([('name', '=', newyear)])

        newstartdate = datetime.datetime(fiscalyear_record.date_start.year, fiscalyear_record.date_start.month, fiscalyear_record.date_start.day)
        newstartdate = newstartdate + relativedelta(months=12)

        newenddate = datetime.datetime(fiscalyear_record.date_end.year, fiscalyear_record.date_end.month, fiscalyear_record.date_end.day)
        newenddate = newenddate + relativedelta(months=12)
        if not newfiscalyear:
            fiscalyear_data = {
                'name': newyear,
                'company_id': self.env.user.company_id.id,
                'date_start': newstartdate,
                'date_end': newenddate,
                'state': '1'
            }
            period_ids = self.env['ps.account.period'].search([('year', '=', cur_year)])
            index = 0
            period_data = []
            for item in period_ids:
                newdate1 = datetime.datetime.strptime(item.date_start, '%Y-%m-%d')
                newdate1 = newdate1 + relativedelta(months=12)
                newdate2 = datetime.datetime.strptime(item.date_end, '%Y-%m-%d')
                newdate2 = newdate2 + relativedelta(months=12)

                index = index + 1
                if index == 1:
                    financial_state = '1'
                else:
                    financial_state = '0'
                temp_data = {
                    'company_id': self.env.user.company_id.id,
                    'period': item.period,
                    'date_start': newdate1,
                    'date_end': newdate2,
                    'financial_state': financial_state,
                    'business_state': '0',
                }
                period_data.append((0, 0, temp_data))
            fiscalyear_data['period_ids'] = period_data
            self.env['ps.account.fiscalyear'].create(fiscalyear_data)
        else:
            index = 0
            period_ids = newfiscalyear.period_ids
            for item in period_ids:
                index = index + 1
                if index == 1:
                    item.financial_state = '1'
                else:
                    item.financial_state = '0'

        #2、 科目表处理,Odoo中公司+科目编号是唯一的，讨论后再处理

        #3、生成期初凭证，要月结年度科目余额不等于0的结转到凭证中，余额在哪方就放在哪方，要考虑辅助核算
        sql = """select mx.account_id,sum(balance) as balance, 
                 sum(amount_currency) as currency_balance,sum(quantity) as quantity_balance,mx.currency_id,mx.partner_id,
                 product_id from account_move_line mx 
                 left join account_move hz on mx.move_id=hz.id 
                 left join account_account account on mx.account_id=account.id 
                 left join ps_account_period pe on hz.ps_period_code=pe.id
                 where pe.year='%s' 
                 group by mx.account_id,account.code,mx.currency_id,mx.partner_id,
                 product_id
                 having sum(balance)!=0 """ % (cur_year)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        if len(temp_ids) > 0:
            default_journal = self.env['account.journal'].search([('type', '=', 'general'),
                                                                  ('company_id', '=', self.env.user.company_id.id)],
                                                                 limit=1)
            if not default_journal:
                raise UserError(_("Please create a generic book type first!"))
            new_period_id = self.env['ps.account.period'].search([('year', '=', newyear), ('period', '=','01')], limit=1)
            if not new_period_id:
                raise UserError(_("No period of 01 found in the new fiscal year"))

            new_account_move_data = {
                'name': _('opening move'),
                'company_id': self.env.user.company_id.id,
                'journal_id': default_journal.id,
                # 'ps_period_year': newyear,
                # 'ps_period_code': '01',
                'date': new_period_id.date_start
            }
            new_line_ids_data = []
            for record in temp_ids:
                debit = 0
                credit = 0
                balance = record[1]
                # 外币
                # debit_currency = 0
                # credit_currency = 0
                amount_currency = record[2]
                # 数量
                # debit_quantity = 0
                # credit_quantity = 0
                quantity = record[3]
                if record[1] > 0:
                    debit = record[1]
                    # debit_currency = record[2]
                    # debit_quantity = record[3]
                else:
                    credit = -record[1]
                    # credit_currency = -record[2]
                    # credit_quantity = -record[3]

                new_line_ids_data.append((0, 0, {
                    'name': _('opening account balance'),
                    'company_id': self.env.user.company_id.id,
                    'journal_id': default_journal.id,
                    'account_id': record[0],
                    'debit': debit,
                    'credit': credit,
                    'balance': balance,

                    # 'debit_currency': debit_currency,
                    # 'credit_currency': credit_currency,
                    'amount_currency': amount_currency,

                    # 'debit_quantity': debit_quantity,
                    # 'credit_quantity': credit_quantity,
                    'quantity': quantity,
                    'ref': _('opening move'),

                    'currency_id': record[4],
                    'partner_id': record[5],
                    'product_id': record[6],
                }))
            new_account_move_data['line_ids'] = new_line_ids_data

            new_account_move = self.env['account.move'].with_context(
                {'check_move_validity': False, 'background_code_generate': '1'}).create(new_account_move_data)
            self.env['res.company'].search([('id', '=', self.env.user.company_id.id)], limit=1).write({'account_opening_move_id': new_account_move.id})
        return True

    @api.model
    def ps_period_end_check(self,cur_kjqj):
        checkresult = True
        cur_year = cur_kjqj[0:4]
        cur_period = cur_kjqj[4:]
        period_ids = self.env['ps.account.period'].search(
            [('year', '<=', cur_year), ('period', '<', cur_period), ('financial_state', '!=', '2')])
        if len(period_ids) >= 1:
            checkresult = False
            raise ValidationError(_('There is an unsettled period before the current selection period, please process the previous period first!'))
        period_ids = self.env['ps.account.period'].search(
            [('year', '=', cur_year), ('period', '=', cur_period), ('financial_state', '=', '2')])
        if len(period_ids) >= 1:
            checkresult = False
            raise ValidationError(cur_year + _('year') + cur_period + _('period is checked out'))
        period_end_check_data = []
        account_move_state = []
        # 1、检查凭证状态
        # 待审核
        sql = """select count(*) from account_move a left join ps_account_period b on a.ps_period_code = b.id where b.year='%s' and b.period='%s' and name <>'00000' and state='draft' """ % (cur_year, cur_period)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        draft_bill_count = temp_ids[0][0]
        if draft_bill_count == 0:
            account_move_state.append({'name': _('Pending certificate'), 'content': str(draft_bill_count) + _('piece'), 'status': '0'})
        else:
            checkresult = False
            account_move_state.append({'name': _('Pending certificate'), 'content': str(draft_bill_count) + _('piece'), 'status': '2'})
        # 待记账
        sql = """select count(*) from account_move a left join ps_account_period b on a.ps_period_code = b.id where b.year='%s' and b.period='%s' and name <>'00000' and state='checked' """ % (cur_year, cur_period)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        checked_bill_count = temp_ids[0][0]
        if checked_bill_count == 0:
            account_move_state.append({'name': _('Pending voucher'), 'content': str(draft_bill_count) + _('piece'), 'status': '0'})
        else:
            checkresult = False
            account_move_state.append({'name': _('Pending voucher'), 'content': str(checked_bill_count) + _('piece'), 'status': '2'})
        period_end_check_data.append({'name': _('Voucher status'), 'content': account_move_state})

        # 2、检查损益类科目是否已经结转
        profit_loss_attribute_id = self.env.user.company_id.profit_loss_attribute_id
        if not profit_loss_attribute_id:
            profit_loss_attribute_id = '5'  # 此参数的值和科目一起预置，正常情况下用不到
        sql = """select account.ps_balance_direction as direction,account.code, mx.account_id,sum(balance) as balance, 
    	                          sum(amount_currency) as currency_balance,sum(quantity) as quantity_balance,mx.currency_id,mx.partner_id
    	                          from account_move_line mx 
    	                          left join account_move hz on mx.move_id=hz.id 
    	                          left join account_account account on mx.account_id=account.id 
    	                          left join ps_account_period d on hz.ps_period_code=d.id
    	                          where account.account_attribute_id=%s and  d.year='%s' and d.period='%s'
    	                          group by mx.account_id,account.code,account.ps_balance_direction  ,mx.currency_id,mx.partner_id
    	                          having sum(balance)!=0 """ % (int(profit_loss_attribute_id), cur_year, cur_period)
        self.env.cr.execute(sql)
        profit_line_ids = self.env.cr.fetchall()
        end_period_and_carry_over = []
        # 自定义结转凭证检查
        period_ids = self.env['ps.account.period'].search(
            [('year', '=', cur_year), ('period', '=', cur_period), ('financial_state', '!=', '2')])
        move = self.env['account.move'].search(
            [('carry_over_head_id', '!=', False), ('date', '>=', period_ids.date_start),
             ('date', '<=', period_ids.date_end)])
        if self.env['ps.account.carry.over.head'].search([]):
            if move:
                end_period_and_carry_over.append({'name': _('Account Carry Over'),
                                                  'content': _('Already generate account carry over'),
                                                  'status': '0'})
            else:
                checkresult = False
                end_period_and_carry_over.append({'name': _('Account Carry Over'),
                                                  'content': _('Ungenerated Account Carry Over'),
                                                  'status': '2'})
        if len(profit_line_ids) > 0:
            # raise ValidationError('损益类科目未结平，请先进行损益结转!')
            end_period_and_carry_over.append({'name': _('Profit and loss carryover'), 'content': _('Unfollowed'), 'status': '1'})
        else:
            end_period_and_carry_over.append({'name': _('Profit and loss carryover'), 'content': _('Already carried over'), 'status': '0'})

        if end_period_and_carry_over:
            period_end_check_data.append({'name': _('End of the period'), 'content': end_period_and_carry_over})

        # 4、资产类科目是否有赤字
        sql = """select account_id,account.code,account.name,sum(balance) balance
    	                from account_move_line mx 
    	                left join account_move hz on mx.move_id=hz.id 
    	                left join account_account account on mx.account_id=account.id 
    	                left join ps_account_period d on hz.ps_period_code=d.id
    	                where account.deprecated=FALSE and d.year='%s' and d.period='%s'
    	                group by mx.account_id,account.code,account.name
    	                HAVING sum(balance)<0 """ % (cur_year, cur_period)

        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        asset_account_data = []
        if len(temp_ids) > 0:
            for item in temp_ids:
                asset_account_data.append({'name': item[0], 'content': item[2]+_(' Deficit:   ')+str(item[3]), 'status': '1'})
                # checkresult = False
                # raise ValidationError('现金银行类科目有赤字!')
        else:
            asset_account_data.append({'name': _('Cash Subject'), 'content': _('No Deficit'), 'status': '0'})
            asset_account_data.append({'name': _('Bank Subject'), 'content': _('No Deficit'), 'status': '0'})
        period_end_check_data.append({'name': _('Asset Class Subject'), 'content': asset_account_data})

        # 3、按凭证字检查凭证断号
        document_no_ids = self.env['ps.account.document.no'].search(
            [('company_id', '=', self.env.user.company_id.id), ('year', '=', cur_year), ('period', '=', cur_period)])
        for docno in document_no_ids:
            sql = """select max(rownumber) as num,max(name) as name from(
            	                        select row_number() OVER(order by name asc) as rownumber, cast (right(name,5) as int) as name from account_move left join ps_account_period on account_move.ps_period_code=ps_account_period.id
            	                        where name!='00000' and ps_account_period.year='%s' and ps_account_period.period='%s' and ps_voucher_word='%s'
            	                        ) temp """ % (cur_year, cur_period, docno.voucher_name)
            self.env.cr.execute(sql)
            temp_ids = self.env.cr.fetchall()
            if temp_ids[0][0] != temp_ids[0][1]:
                checkresult = False
                period_end_check_data.append(
                    {'name': _('Broken Number'), 'content': {'name': _('Broken Number Check'), 'content': _('Broken Number Exists'), 'status': '2'}})
            else:
                period_end_check_data.append(
                    {'name': _('Broken Number'), 'content': {'name': _('Broken Number Check'), 'content': _('No Broken Number'), 'status': '0'}})
        if len(document_no_ids) == 0:
            period_end_check_data.append(
                {'name': _('Broken Number'), 'content': {'name': _('Broken Number Check'), 'content': _('No Broken Number'), 'status': '0'}})
        return checkresult, period_end_check_data

    @api.model
    def ps_period_end_handle(self, cur_kjqj):
        cur_year = cur_kjqj[0:4]
        cur_period = cur_kjqj[4:]
        checkresult,return_data = self.ps_period_end_check(cur_kjqj)
        if checkresult:
            return self._ps_period_month_end(cur_year, cur_period)
        else:
            raise ValidationError('Check failed and settlement is disabled!')

    @api.model
    def ps_period_end_cancel_handle(self, cur_kjqj):
        cur_year = cur_kjqj[0:4]
        cur_period = cur_kjqj[4:]

        sql = """select count(*) from ps_account_period where year||period>'%s' and financial_state='2' """ % (cur_kjqj)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        period_count = temp_ids[0][0]
        if period_count >= 1:
            raise ValidationError(cur_year + _('Year') + cur_period + _('There are settled period before the current period, please handle the previous period!'))
        # 1、将res.company中的当前期间月结标志改为“0,开放”
        # 2、将此期间设置为当前区间（ps.cofig)
        # 3、将此期间月结标志改为“当前期间”
        pscurkjqj = self.env.user.company_id.ps_current_fiscalyear
        pscuryear = pscurkjqj[0:4]
        pscurperiod = pscurkjqj[4:]
        if pscurkjqj:
            self.env['ps.account.period'].search(
                [('year', '=', pscuryear), ('period', '=', pscurperiod), ('company_id', '=', self.env.user.company_id.id)]).write({'financial_state': '0'})
        #更新当前会计期间
        self.env.user.company_id.write({'ps_current_fiscalyear': cur_year+cur_period})
        period_obj = self.env['ps.account.period'].search([('year', '=', cur_year),
                                                           ('period', '=', cur_period), ('company_id', '=', self.env.user.company_id.id)]).write({'financial_state': '1'})
        # 如果是最后一个期间：
        # 1删除自动创建的初始凭证
        # 2修改会计年度为未年结
        # 自动生成的会计期间不删除
        period_ids = self.env['ps.account.period'].search([('year', '=', cur_year), ('period', '>', cur_period)])
        if len(period_ids) == 0:
            newyear = str(int(cur_year) + 1)
            self.env['ps.account.fiscalyear'].search([('name', '=', cur_year),
                                                      ('company_id', '=', self.env.user.company_id.id)]).write({'state': '1'})
            self.env['ps.account.fiscalyear'].search([('name', '=', newyear),
                                                      ('company_id', '=', self.env.user.company_id.id)]).write(
                {'state': '0'})
            period_ids=self.env['ps.account.period'].search([('year', '=', newyear), ('period', '=', '01')])
            if period_ids:
                for r in period_ids:
                    self.env['account.move'].search([('ps_period_code', '=', r.id),
                                             ('name', '=', '00000'), ('company_id', '=', self.env.user.company_id.id)]).unlink()
        return True

    ####################################################
    # rewrite _reverse_move methods
    ####################################################
    @api.multi
    def _reverse_move(self, date=None, journal_id=None):
        self.ensure_one()
        reversed_move = self.copy(default={
            'carry_over_head_id': False,
            'date': date,
            'journal_id': journal_id.id if journal_id else self.journal_id.id,
            'ref': _('reversal of: ') + self.name})
        for acm_line in reversed_move.line_ids.with_context(check_move_validity=False):
            acm_line.write({
                'debit': -acm_line.debit,
                'credit': -acm_line.credit,
                # 'debit_currency': -acm_line.debit_currency,
                # 'credit_currency': -acm_line.credit_currency,
                'amount_currency': -acm_line.amount_currency,
                # 'debit_quantity': -acm_line.debit_quantity,
                # 'credit_quantity': -acm_line.credit_quantity,
                'quantity': -acm_line.quantity,

            })
        if self.carry_over_head_id:
            self.carry_over_head_id = False
        return reversed_move
    @api.multi
    def reverse_moves(self, date=None, journal_id=None):
        date = date or fields.Date.today()
        reversed_moves = self.env['account.move']
        for ac_move in self:
            reversed_move = ac_move._reverse_move(date=date,
                                                  journal_id=journal_id)
            reversed_moves |= reversed_move
            aml = ac_move.line_ids.filtered(lambda x: x.account_id.reconcile or x.account_id.internal_type == 'liquidity')
            aml.remove_move_reconcile()
            #reconcile together the reconciliable (or the liquidity aml) and their newly created counterpart
            for account in list(set([x.account_id for x in aml])):
                to_rec = aml.filtered(lambda y: y.account_id == account)
                to_rec |= reversed_move.line_ids.filtered(lambda y: y.account_id == account)
                #reconciliation will be full, so speed up the computation by using skip_full_reconcile_check in the context
                to_rec.with_context(skip_full_reconcile_check=True).reconcile()
                # to_rec.force_full_reconcile()
        if reversed_moves:
           return [x.id for x in reversed_moves]
        return []