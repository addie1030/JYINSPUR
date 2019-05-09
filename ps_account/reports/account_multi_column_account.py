# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import copy
from odoo.exceptions import ValidationError
from functools import reduce

class AccountChinaMultiColumnAccountReport(models.AbstractModel):
    _name = 'account.china.multi.column.account.report'
    _description = _("Multi Column Account Report")
    _inherit = 'account.china.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_subject = {'subject_from': '1001', 'subject_to': '1001'}
    filter_auxiliary = {'filter': 'all'}

    def _get_columns_name(self, options):
        auxiliary = options.get('auxiliary').get('filter')
        if auxiliary == 'all':
            headers = [
                {'name': _(' Date '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap; width: 8%;background-color:#0073C6;color:white'},
                {'name': _(' Voucher Number '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _('Abstract'), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 19%;background-color:#0073C6;color:white'},
                {'name': _(' Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Direction '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 2%;background-color:#0073C6;color:white'},
                {'name': _(' Balance '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 6%;background-color:#0073C6;color:white'},
                {'name': _(' Product'), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white'},
                {'name': _(' Partner'), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white'},
                {'name': _(' Cash Flow'), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white'}
            ]
        else:
            headers = [
                {'name': _(' Date '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap; width: 8%;background-color:#0073C6;color:white'},
                {'name': _(' Voucher Number '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _('Abstract'), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 25%;background-color:#0073C6;color:white'},
                {'name': _(' Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                {'name': _(' Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                {'name': _(' Direction '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Balance '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                {'name': _(' Auxiliary'), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 25%;background-color:#0073C6;color:white'}
            ]

        return headers

    def _get_report_name(self):
        return _("Multi column account")

    def _get_templates(self):
        templates = super(AccountChinaMultiColumnAccountReport, self)._get_templates()
        templates['main_template'] = 'ps_account.template_multi_column_account_reports'
        try:
            self.env['ir.ui.view'].get_view_id('ps_account.template_account_china_multi_column_account_line_report')
            templates['line_template'] = 'ps_account.template_account_china_multi_column_account_line_report'
            templates['search_template'] = 'ps_account.search_template_china'
        except ValueError:
            pass
        return templates

    @api.model
    def _get_lines(self, options, line_id=None):
        date_from = options.get('date').get('date_from')
        date_to = options.get('date').get('date_to')
        subject_from = options.get('subject').get('subject_from')
        subject_to = options.get('subject').get('subject_to')
        auxiliary = options.get('auxiliary').get('filter')

        lines = []
        res = []
        rows = []
        str_info = _('Query Criteria:')
        auxiliary_info = _('Auxiliary:')
        date_info = _('  Date:') + date_from + ' - ' + date_to
        account_info = _('  Account:') + subject_from + ' - ' + subject_to
        product = ''
        partner = ''
        cashflow = ''

        row = 1
        period_last = ''
        period_current = ''
        total_all_debit = 0.00
        total_all_credit = 0.00
        total_current_debit = 0.00
        total_current_credit = 0.00

        #当前日期所在会计年度的开始日期，然后统计年初余额，业务发生日期小于搜素到的开始日期
        date_start = self.env['ps.account.fiscalyear'].search([('date_start', '<=', date_from),
                                                               ('date_end', '>=', date_from)]).date_start
        if not date_start:
            date_start = date_from

        if auxiliary == 'all':
            str_info += auxiliary_info + _('All') + '  ' + date_info + account_info
            sql = """
                    SELECT hz.date as date,hz.name as name,mx.name as summary,mx.debit as debit,mx.credit as credit,
                    (CASE  WHEN mx.balance > 0 THEN '借' WHEN mx.balance < 0 THEN '贷' ELSE '平'END) as direction,abs(mx.balance) as balance, 
                    mx.product_id as product_id, mx.partner_id as partner_id, mx.cash_flow_item_id as cash_flow_item_id               
                    FROM account_move hz
                    LEFT JOIN account_move_line mx ON mx.move_id=hz.id
                    LEFT JOIN account_account account ON mx.account_id=account.id
                    WHERE hz.state ='posted' and account.code >= '""" + subject_from + """' AND account.code <= '""" + subject_to + 'zzzzzzzz'+"""' AND hz.NAME <> '00000' AND hz.date >= '"""+str(date_from)+"""' AND hz.date <= '"""+str(date_to)+"""' 
                    ORDER BY hz.date,hz.name
                    """
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()

            sql1 = """
                    SELECT sum(mx.debit) as total_debit,sum(mx.credit) as total_credit
                    FROM account_move hz
                    LEFT JOIN account_move_line mx ON mx.move_id=hz.id
                    LEFT JOIN account_account account ON mx.account_id=account.id
                    WHERE hz.state ='posted' and account.code >= '""" + subject_from + """' AND account.code <= '""" + subject_to + 'zzzzzzzz'+"""' AND hz.date < '"""+str(date_start)+"""'
                 """
            self.env.cr.execute(sql1)
            resone = self.env.cr.fetchone()

            if resone:
                total_all_debit = resone[0]
                total_all_credit = resone[1]

        if auxiliary == 'partner':
            str_info += auxiliary_info + _('Partner') + '  ' + date_info + account_info
            sql = """
                    SELECT hz.date as date,hz.name as name,mx.name as summary,mx.debit as debit,mx.credit as credit,
                    (CASE  WHEN mx.balance > 0 THEN '借' WHEN mx.balance < 0 THEN '贷' ELSE '平'END) as direction,abs(mx.balance) as balance, 
                    rp.id as partner               
                    FROM account_move hz
                    LEFT JOIN account_move_line mx ON mx.move_id=hz.id
                    LEFT JOIN account_account account ON mx.account_id=account.id
                    left join res_partner rp on mx.partner_id = rp.id
                    WHERE hz.state ='posted' and mx.partner_id is not null and account.code >= '""" + subject_from + """' AND account.code <= '""" + subject_to + 'zzzzzzzz' + """' AND hz.NAME <> '00000' AND hz.date >= '""" + str(
                            date_from) + """' AND hz.date <= '""" + str(date_to) + """' 
                                ORDER BY hz.date,hz.name
                                """
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()

            sql1 = """
                    SELECT sum(mx.debit) as total_debit, sum(mx.credit) as total_credit          
                    FROM account_move hz
                    LEFT JOIN account_move_line mx ON mx.move_id=hz.id
                    LEFT JOIN account_account account ON mx.account_id=account.id
                    left join res_partner rp on mx.partner_id = rp.id
                    WHERE hz.state ='posted' and mx.partner_id is not null and account.code >= '""" + subject_from + """' AND account.code <= '""" + subject_to + 'zzzzzzzz' + """'  
                    AND hz.date < '""" + str(date_start) + """' 
                    """
            self.env.cr.execute(sql1)
            resone = self.env.cr.fetchone()

            if resone:
                total_all_debit = resone[0]
                total_all_credit = resone[1]

        if auxiliary == 'product':
            str_info += auxiliary_info + _('Product') + '  ' + date_info + account_info
            sql = """
                    SELECT hz.date as date,hz.name as name,mx.name as summary,mx.debit as debit,mx.credit as credit,
                    (CASE  WHEN mx.balance > 0 THEN '借' WHEN mx.balance < 0 THEN '贷' ELSE '平'END) as direction,abs(mx.balance) as balance, 
                    pp.id as product               
                    FROM account_move hz
                    LEFT JOIN account_move_line mx ON mx.move_id=hz.id
                    LEFT JOIN account_account account ON mx.account_id=account.id
                    left join product_template pp on mx.product_id = pp.id
                    WHERE hz.state ='posted' and mx.product_id is not null and account.code >= '""" + subject_from + """' AND account.code <= '""" + subject_to + 'zzzzzzzz' + """' AND hz.NAME <> '00000' AND hz.date >= '""" + str(
                    date_from) + """' AND hz.date <= '""" + str(date_to) + """' 
                                ORDER BY hz.date,hz.name
                                            """
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()

            sql1 = """
                        SELECT sum(mx.debit) as total_debit, sum(mx.credit) as total_credit          
                        FROM account_move hz
                        LEFT JOIN account_move_line mx ON mx.move_id=hz.id
                        LEFT JOIN account_account account ON mx.account_id=account.id
                        left join product_template pp on mx.product_id = pp.id
                        WHERE hz.state ='posted' and mx.product_id is not null and account.code >= '""" + subject_from + """' AND account.code <= '""" + subject_to + 'zzzzzzzz' + """'  
                                AND hz.date < '""" + str(date_start) + """' 
                                """
            self.env.cr.execute(sql1)
            resone = self.env.cr.fetchone()

            if resone:
                total_all_debit = resone[0]
                total_all_credit = resone[1]

        if auxiliary == 'cashflow':
            str_info += auxiliary_info + _('Cash Flow') + '  ' + date_info + account_info
            sql = """
                    SELECT hz.date as date,hz.name as name,mx.name as summary,mx.debit as debit,mx.credit as credit,
                    (CASE  WHEN mx.balance > 0 THEN '借' WHEN mx.balance < 0 THEN '贷' ELSE '平'END) as direction,abs(mx.balance) as balance, 
                    cf.id as cashflow               
                    FROM account_move hz
                    LEFT JOIN account_move_line mx ON mx.move_id=hz.id
                    LEFT JOIN account_account account ON mx.account_id=account.id
                    left join ps_cashflow_item cf on mx.cash_flow_item_id = cf.id
                    WHERE hz.state ='posted' and mx.cash_flow_item_id is not null and account.code >= '""" + subject_from + """' AND account.code <= '""" + subject_to + 'zzzzzzzz' + """' AND hz.NAME <> '00000' AND hz.date >= '""" + str(
                    date_from) + """' AND hz.date <= '""" + str(date_to) + """' 
                                ORDER BY hz.date,hz.name
                    """
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()

            sql1 = """
                    SELECT sum(mx.debit) as total_debit, sum(mx.credit) as total_credit          
                    FROM account_move hz
                    LEFT JOIN account_move_line mx ON mx.move_id=hz.id
                    LEFT JOIN account_account account ON mx.account_id=account.id
                    left join ps_cashflow_item cf on mx.cash_flow_item_id = cf.id
                    WHERE hz.state ='posted' and mx.cash_flow_item_id is not null and account.code >= '""" + subject_from + """' AND account.code <= '""" + subject_to + 'zzzzzzzz' + """'  
                            AND hz.date < '""" + str(date_start) + """' 
                            """
            self.env.cr.execute(sql1)
            resone = self.env.cr.fetchone()

            if resone:
                total_all_debit = resone[0]
                total_all_credit = resone[1]

        if not total_all_debit:
            total_all_debit = 0
        if not total_all_credit:
            total_all_credit = 0

        if total_all_debit > total_all_credit:
            direction_qc = '借'
        elif total_all_debit < total_all_credit:
            direction_qc = '贷'
        else:
            direction_qc = '平'


        l = len(res)
        count = 1

        if res:
            if auxiliary == 'all':
                for r in res:
                    if r[7]:
                        product = self.env['product.product'].browse(r[7]).name
                    else:
                        product = ''
                    if r[8]:
                        partner = self.env['res.partner'].browse(r[8]).name
                    else:
                        partner = ''
                    if r[9]:
                        cashflow = self.env['ps.cashflow.item'].browse(r[9]).name
                    else:
                        cashflow = ''

                    if count == 1:
                        period_current = r[0].strftime("%Y-%m-%d")[0:7]
                        period_last = r[0].strftime("%Y-%m-%d")[0:7]
                    else:
                        period_current = r[0].strftime("%Y-%m-%d")[0:7]

                    if (period_current == period_last) and (count == 1):
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d")[0:7],
                            'name': '',
                            'summary': "年初余额",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction_qc,
                            'balance': abs(total_all_debit - total_all_credit),
                            'product': '',
                            'partner': '',
                            'cashflow': ''
                        })
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'product': product,
                            'partner': partner,
                            'cashflow': cashflow
                        })
                        count += 1
                    elif (period_current == period_last) and (count != 1) and (count != l):
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'product': product,
                            'partner': partner,
                            'cashflow': cashflow
                        })
                        count += 1
                    elif (period_current != period_last) and (count < l):
                        if total_current_debit > total_current_credit:
                            direction = '借'
                        elif total_current_debit < total_current_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': period_last,
                            'name': '',
                            'summary': "本期合计",
                            'debit': total_current_debit,
                            'credit': total_current_credit,
                            'direction': direction,
                            'balance': abs(total_current_debit - total_current_credit),
                            'product': '',
                            'partner': '',
                            'cashflow': ''
                        })
                        total_all_debit = total_all_debit + total_current_debit
                        total_all_credit = total_all_credit + total_current_credit
                        if total_all_debit > total_all_credit:
                            direction = '借'
                        elif total_all_debit < total_all_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': period_last,
                            'name': '',
                            'summary': "本年累计",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction,
                            'balance': abs(total_all_debit - total_all_credit),
                            'product': '',
                            'partner': '',
                            'cashflow': ''
                        })
                        count += 1
                        period_last = period_current
                        total_current_debit = 0.00
                        total_current_credit = 0.00
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'product': product,
                            'partner': partner,
                            'cashflow': cashflow
                        })
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]
                    elif (period_current == period_last) and (count == l):
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]
                        row += 1
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'product': product,
                            'partner': partner,
                            'cashflow': cashflow
                        })

                        if total_current_debit > total_current_credit:
                            direction = '借'
                        elif total_current_debit < total_current_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': period_current,
                            'name': '',
                            'summary': "本期合计",
                            'debit': total_current_debit,
                            'credit': total_current_credit,
                            'direction': direction,
                            'balance': abs(total_current_debit - total_current_credit),
                            'product': '',
                            'partner': '',
                            'cashflow': ''
                        })
                        total_all_debit = total_all_debit + total_current_debit
                        total_all_credit = total_all_credit + total_current_credit
                        if total_all_debit > total_all_credit:
                            direction = '借'
                        elif total_all_debit < total_all_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': period_current,
                            'name': '',
                            'summary': "本年累计",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction,
                            'balance': abs(total_all_debit - total_all_credit),
                            'product': '',
                            'partner': '',
                            'cashflow': ''
                        })

            else:
                for r in res:
                    if auxiliary == 'cashflow':
                        if r[7]:
                            auxiliary_name = self.env['ps.cashflow.item'].browse(r[7]).name
                        else:
                            auxiliary_name = ''
                    if auxiliary == 'product':
                        if r[7]:
                            auxiliary_name = self.env['product.template'].browse(r[7]).name
                        else:
                            auxiliary_name = ''
                    if auxiliary == 'partner':
                        if r[7]:
                            auxiliary_name = self.env['res.partner'].browse(r[7]).name
                        else:
                            auxiliary_name = ''

                    if count == 1:
                        period_current = r[0].strftime("%Y-%m-%d")[0:7]
                        period_last = r[0].strftime("%Y-%m-%d")[0:7]
                    else:
                        period_current = r[0].strftime("%Y-%m-%d")[0:7]

                    if (period_current == period_last) and (count == 1) and (count == l):
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d")[0:7],
                            'name': '',
                            'summary': "年初余额",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction_qc,
                            'balance': abs(total_all_debit - total_all_credit),
                            'auxiliary': ''
                        })
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'auxiliary': auxiliary_name
                        })
                        total_all_debit = total_all_debit + total_current_debit
                        total_all_credit = total_all_credit + total_current_credit
                        if total_current_debit > total_current_credit:
                            direction = '借'
                        elif total_current_debit < total_current_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d")[0:7],
                            'name': '',
                            'summary': "本期合计",
                            'debit': total_current_debit,
                            'credit': total_current_credit,
                            'direction': direction,
                            'balance': abs(total_current_debit - total_current_credit),
                            'auxiliary': ''
                        })
                        if total_all_debit > total_all_credit:
                            direction = '借'
                        elif total_all_debit < total_all_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d")[0:7],
                            'name': '',
                            'summary': "本年累计",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction,
                            'balance': abs(total_all_debit - total_all_credit),
                            'auxiliary': ''
                        })
                        total_current_debit = 0.00
                        total_current_credit = 0.00

                    elif (period_current == period_last) and (count == 1) and (count != l):
                        period_last = period_current
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d")[0:7],
                            'name': '',
                            'summary': "年初余额",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction_qc,
                            'balance': abs(total_all_debit - total_all_credit),
                            'auxiliary': ''
                        })
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'auxiliary': auxiliary_name
                        })
                        count += 1
                    elif (period_current == period_last) and (count != 1) and (count != l):
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'auxiliary': auxiliary_name
                        })
                        count += 1

                    elif (period_current != period_last) and (count < l):
                        if total_current_debit > total_current_credit:
                            direction = '借'
                        elif total_current_debit < total_current_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': period_last,
                            'name': '',
                            'summary': "本期合计",
                            'debit': total_current_debit,
                            'credit': total_current_credit,
                            'direction': direction,
                            'balance': abs(total_current_debit - total_current_credit),
                            'auxiliary': ''

                        })

                        total_all_debit = total_all_debit + total_current_debit
                        total_all_credit = total_all_credit + total_current_credit
                        if total_all_debit > total_all_credit:
                            direction = '借'
                        elif total_all_debit < total_all_credit:
                            direction = '贷'
                        else:
                            direction = '平'

                        rows.append({
                            'date': period_last,
                            'name': '',
                            'summary': "本年累计",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction,
                            'balance': abs(total_all_debit - total_all_credit),
                            'auxiliary': ''
                        })
                        count += 1
                        period_last = period_current
                        total_current_debit = 0.00
                        total_current_credit = 0.00
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'auxiliary': auxiliary_name
                        })
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]

                    elif (period_current == period_last) and (count == l):
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'auxiliary': auxiliary_name
                        })

                        if total_current_debit > total_current_credit:
                            direction = '借'
                        elif total_current_debit < total_current_credit:
                            direction = '贷'
                        else:
                            direction = '平'

                        rows.append({
                            'date': period_current,
                            'name': '',
                            'summary': "本期合计",
                            'debit': total_current_debit,
                            'credit': total_current_credit,
                            'direction': direction,
                            'balance': abs(total_current_debit - total_current_credit),
                            'auxiliary': ''

                        })

                        total_all_debit = total_all_debit + total_current_debit
                        total_all_credit = total_all_credit + total_current_credit
                        if total_all_debit > total_all_credit:
                            direction = '借'
                        elif total_all_debit < total_all_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': period_current,
                            'name': '',
                            'summary': "本年累计",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction,
                            'balance': abs(total_all_debit - total_all_credit),
                            'auxiliary': ''

                        })
                    elif (period_current != period_last) and (count == l):
                        if total_current_debit > total_current_credit:
                            direction = '借'
                        elif total_current_debit < total_current_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': period_last,
                            'name': '',
                            'summary': "本期合计",
                            'debit': total_current_debit,
                            'credit': total_current_credit,
                            'direction': direction,
                            'balance': abs(total_current_debit - total_current_credit),
                            'auxiliary': ''

                        })

                        total_all_debit = total_all_debit + total_current_debit
                        total_all_credit = total_all_credit + total_current_credit
                        if total_all_debit > total_all_credit:
                            direction = '借'
                        elif total_all_debit < total_all_credit:
                            direction = '贷'
                        else:
                            direction = '平'

                        rows.append({
                            'date': period_last,
                            'name': '',
                            'summary': "本年累计",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction,
                            'balance': abs(total_all_debit - total_all_credit),
                            'auxiliary': ''
                        })
                        count += 1
                        period_last = period_current
                        total_current_debit = 0.00
                        total_current_credit = 0.00
                        rows.append({
                            'date': r[0].strftime("%Y-%m-%d"),
                            'name': r[1],
                            'summary': r[2],
                            'debit': r[3],
                            'credit': r[4],
                            'direction': r[5],
                            'balance': r[6],
                            'auxiliary': auxiliary_name
                        })
                        total_current_debit = total_current_debit + r[3]
                        total_current_credit = total_current_credit + r[4]

                        if total_current_debit > total_current_credit:
                            direction = '借'
                        elif total_current_debit < total_current_credit:
                            direction = '贷'
                        else:
                            direction = '平'
                        rows.append({
                            'date': period_current,
                            'name': '',
                            'summary': "本期合计",
                            'debit': total_current_debit,
                            'credit': total_current_credit,
                            'direction': direction,
                            'balance': abs(total_current_debit - total_current_credit),
                            'auxiliary': ''

                        })

                        total_all_debit = total_all_debit + total_current_debit
                        total_all_credit = total_all_credit + total_current_credit
                        if total_all_debit > total_all_credit:
                            direction = '借'
                        elif total_all_debit < total_all_credit:
                            direction = '贷'
                        else:
                            direction = '平'

                        rows.append({
                            'date': period_current,
                            'name': '',
                            'summary': "本年累计",
                            'debit': total_all_debit,
                            'credit': total_all_credit,
                            'direction': direction,
                            'balance': abs(total_all_debit - total_all_credit),
                            'auxiliary': ''
                        })

        lines.append({
            'id': 999,
            'type': auxiliary,
            'name': str_info,
            'columns': rows
        })
        return lines
