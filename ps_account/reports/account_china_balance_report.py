from odoo import models, fields, api, _
import copy
from odoo.exceptions import ValidationError


class ReportAccountChinaBalanceReport(models.AbstractModel):
    _name = "account.china.balance.report"
    _description = _("浪潮PS科目余额账")
    _inherit = 'account.china.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_subject = {'subject_from': '1001', 'subject_to': '1001'}
    filter_style = {'filter': 'aa'}

    def _get_columns_name(self, options):
        style = options.get('style').get('filter')
        if style == "aa":
            headers = [[
                {'name': _(' Subject Number '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Subject Name '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 12%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Opening balance '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 26%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Current Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 26%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Final Balance '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 26%;background-color:#0073C6;color:white',
                 'colspan': '2'}
            ],
            [
                {'name': _(' Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 13%;background-color:#0073C6;color:white '},
                {'name': _(' Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 13%;background-color:#0073C6;color:white'},
                {'name': _(' Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 13%;background-color:#0073C6;color:white'},
                {'name': _(' Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 13%;background-color:#0073C6;color:white'},
                {'name': _(' Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 13%;background-color:#0073C6;color:white'},
                {'name': _(' Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 13%;background-color:#0073C6;color:white'}
            ]]
        elif style == "bb":
            headers = [[
                {'name': _(' Subject Number '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap; width: 4%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Subject Name '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 9%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 3%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Initial Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Initial Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Current Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Current Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Final Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Final Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'}
            ],
            [
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
            ]]
        elif style == "cc":
            headers = [[
                {'name': _(' Subject Number '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap; width: 7%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Subject Name '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 9%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Initial Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Initial Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Current Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Current Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Final Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'},
                {'name': _(' Final Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white',
                 'colspan': '2'}
            ],
            [
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
            ]]
        elif style == "dd":
            headers = [[
                {'name': _(' Subject Number '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap; width: 3%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Subject Name '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 2%;background-color:#0073C6;color:white',
                 'rowspan': '2'},
                {'name': _(' Initial Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                 'colspan': '3'},
                {'name': _(' Initial Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                 'colspan': '3'},
                {'name': _(' Current Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                 'colspan': '3'},
                {'name': _(' Current Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                 'colspan': '3'},
                {'name': _(' Final Debit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                 'colspan': '3'},
                {'name': _(' Final Credit '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                 'colspan': '3'}
            ],
            [
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Foreign Currency '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            ]]
        return headers

    def _get_report_name(self):
        return _("Account balance account")

    def _get_templates(self):
        templates = super(ReportAccountChinaBalanceReport, self)._get_templates()
        templates['main_template'] = 'ps_account.template_balance_reports'
        try:
            self.env['ir.ui.view'].get_view_id('ps_account.template_account_china_balance_line_report')
            templates['line_template'] = 'ps_account.template_account_china_balance_line_report'
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

        lines = []
        line_num = 1
        # 获取选定区间所有的科目
        sql = """
            SELECT code, name, ps_consider_product, currency_id FROM account_account where code >= '"""+subject_from+"""' AND code <= '"""+subject_to+'zzzzzzzz'+"""'
            ORDER BY code
        """
        self.env.cr.execute(sql)
        subjects = self.env.cr.fetchall()
        if options.get('style').get('filter') == "cc":
            num = True
            num1 = False
            num2 = False
            num3 = False
        elif options.get('style').get('filter') == "bb":
            num1 = True
            num = False
            num2 = False
            num3 = False
        elif options.get('style').get('filter') == "dd":
            num2 = True
            num1 = False
            num = False
            num3 = False
        else:
            num = False
            num1 = False
            num2 = False
            num3 = True

        sql = """
                   SELECT COUNT(*) FROM ACCOUNT_MOVE
                """
        self.env.cr.execute(sql)
        recordCount = self.env.cr.fetchone()[0]

        if len(subjects) <= 0 or recordCount == 0:
            lines.append({
                'id': line_num,
                'name': "",
                'class': '',
                'level': 0,
                'num': num,
                'num1': num1,
                'num2': num2,
                'num3': num3,
                'columns': [],
            })
        else:
            if options.get('style').get('filter') == "cc":
                num = True
                num1 = False
                num2 = False
                num3 = False
            elif options.get('style').get('filter') == "bb":
                num1 = True
                num = False
                num2 = False
                num3 = False
            elif options.get('style').get('filter') == "dd":
                num2 = True
                num1 = False
                num = False
                num3 = False
            else:
                num = False
                num1 = False
                num2 = False
                num3 = True
            rows = self._get_row(date_from, date_to, subject_from, subject_to)
            lines.append({
                'id': line_num,
                'class': '',
                'level': 0,
                'num': num,
                'num1': num1,
                'num2': num2,
                'num3': num3,
                'columns': rows,
            })
        return lines

    def _get_row(self, date_from, date_to, subject_from, subject_to):
        result = []
        sample = {'code': '', 'name': '', 'currency_name': '', 'quantity': 0, 'amount_currency': 0,  'open_balance_debit': 0, 'open_balance_credit': 0, 'cur_debit': 0, 'cur_credit': 0, 'ending_balance_debit': 0, 'ending_balance_credit': 0}
        sql = """
            SELECT code, name, ps_account_level as level FROM account_account where code >= '"""+subject_from+"""' AND code <= '"""+subject_to+'zzzzzzzz'+"""'
            ORDER BY code
        """
        summary = copy.copy(sample)
        summary_open_debit = 0
        summary_open_credit = 0
        summary_cur_debit = 0
        summary_cur_credit = 0
        summary_ending_debit = 0
        summary_ending_credit = 0
        # 这里将最大的code+zzz是为了保证取到最大code的下级科目
        self.env.cr.execute(sql)
        subjects = self.env.cr.fetchall()
        for i in range(len(subjects)):
            subject = subjects[i]
            subject_code = subject[0]
            subject_name = subject[1]
            level = subject[2]
            item = copy.copy(sample)
            open_balance = self._get_opening_balance(subject_code, date_from)
            cur_occurs = self._get_cur_occurs(date_from, date_to, subject_code)
            ending_balance = self._get_ending_balance(open_balance, cur_occurs)
            item['code'] = subject_code
            item['name'] = subject_name
            item['currency_name'] = ending_balance['currency_name']
            item['open_balance_debit'] = round(open_balance['opening_debit'],2)
            item['open_balance_credit'] = round(open_balance['opening_credit'],2)
            item['amount_currency'] = round(open_balance['amount_currency'], 2)
            item['quantity'] = round(open_balance['quantity'], 2)
            item['cur_debit'] = round(cur_occurs['cur_debit'],2)
            item['cur_credit'] = round(cur_occurs['cur_credit'],2)
            item['amount_currency'] = round(cur_occurs['amount_currency'], 2)
            item['quantity'] = round(cur_occurs['quantity'], 2)
            item['ending_balance_debit'] = round(ending_balance['ending_balance_debit'],2)
            item['ending_balance_credit'] = round(ending_balance['ending_balance_credit'],2)
            item['amount_currency'] = round(cur_occurs['amount_currency'], 2)
            item['quantity'] = round(cur_occurs['quantity'], 2)
            result.append(item)
            if(level == 1):
                summary_open_debit += open_balance['opening_debit']
                summary_open_credit += open_balance['opening_credit']
                summary_cur_debit += cur_occurs['cur_debit']
                summary_cur_credit += cur_occurs['cur_credit']
                summary_ending_debit += ending_balance['ending_balance_debit']
                summary_ending_credit += ending_balance['ending_balance_credit']
            # result.reverse()
        summary['code'] = _('Total')
        summary['name'] = ''
        summary['open_balance_debit'] = round(summary_open_debit,2)
        summary['open_balance_credit'] = round(summary_open_credit,2)
        summary['cur_debit'] = round(summary_cur_debit,2)
        summary['cur_credit'] = round(summary_cur_credit,2)
        summary['ending_balance_debit'] = round(summary_ending_debit,2)
        summary['ending_balance_credit'] = round(summary_ending_credit,2)
        result.append(summary)
        return result

    def _get_opening_balance(self, subject, date_from):
        #  需要根据科目编号 去找科目ID  再根据科目ID 去找凭证分录 这个麻烦...
        # fiscalyear中state为2的表示已经年结，会在凭证表中新增一条0000的记录，会计区间是下一年的01期
        # date_from = self._get_exactDay("START", date_from)
        sql = """
            SELECT ps_balance_direction as direction
            FROM ACCOUNT_ACCOUNT 
            WHERE code = '"""+subject+"""'
        """
        # self.env['account.account'].search([('code', '=', subject)])
        self.env.cr.execute(sql)
        temp = self.env.cr.fetchone()
        ls_direction = temp[0]
        sql = """
            SELECT min(B.YEAR) as year
            FROM account_move A
            LEFT JOIN PS_ACCOUNT_PERIOD B ON A.PS_PERIOD_CODE = B.ID
        """
        self.env.cr.execute(sql)
        temp = self.env.cr.fetchone()
        ls_year = temp[0]
        if ls_year == None:
            raise ValidationError(_('No new data for the voucher, please add a new voucher'))
        sql = """
            SELECT min(B.PERIOD) as month
            FROM account_move A
            LEFT JOIN PS_ACCOUNT_PERIOD B ON A.PS_PERIOD_CODE = B.ID
            WHERE B.YEAR = '"""+ls_year+"""'
        """
        self.env.cr.execute(sql)
        ls_month = self.env.cr.fetchone()[0]

        sql = """
            SELECT max(name) as name FROM ps_account_fiscalyear where state = '2'
        """
        self.env.cr.execute(sql)
        year = self.env.cr.fetchone()[0]
        if(year):
            #  如果存在年结，去找生成的下一年的期初凭证
            sql = """
                SELECT SUM(A.debit) AS debit,SUM(A.credit) AS credit,A.DATE AS vsdate, (CASE C.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
                FROM ACCOUNT_MOVE_LINE A 
                LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
                LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
                LEFT  JOIN PS_ACCOUNT_PERIOD D ON B.PS_PERIOD_CODE = D.ID
                WHERE C.CODE LIKE '"""+subject+"""%' AND B.NAME='00000' AND D.YEAR = '"""+str(int(year)+1)+"""'
                GROUP BY vsdate, direction
            """
            self.env.cr.execute(sql)
            ls_row = self.env.cr.fetchone()
            tmp_debit = ls_row[0] or 0.0
            tmp_credit = ls_row[1] or 0.0
            # 找那一期的开始日期
            ls_startday = str(self._get_exactDay("START", (str(year) + '01')))
        else:
            sql = """
                SELECT SUM(A.debit) AS debit,SUM(A.credit) AS credit,D.YEAR AS ps_period_year,D.PERIOD AS ps_period_code,  C.ps_balance_direction as direction
                FROM ACCOUNT_MOVE_LINE A 
                LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
                LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
                LEFT  JOIN PS_ACCOUNT_PERIOD D ON B.PS_PERIOD_CODE = D.ID
                WHERE C.CODE LIKE '""" + subject + """%' AND B.NAME='00000'
                GROUP BY D.YEAR, D.PERIOD, direction
            """
            self.env.cr.execute(sql)
            row = self.env.cr.fetchone()
            if(row):
                tmp_debit = row[0] or 0.0
                tmp_credit = row[1] or 0.0
                ls_balance = row[4]
                ls_startday = str(self._get_exactDay("START", (str(row[2]) + str(row[3]))))
            else:
                tmp_debit = 0.0
                tmp_credit = 0.0
                ls_balance = ls_direction
                ls_startday = str(self._get_exactDay("START", (str(ls_year) + str(ls_month))))
        sql = """
            SELECT SUM(A.debit) AS debit,SUM(A.credit) AS credit,quantity, amount_currency,D.name as currency_name,C.ps_balance_direction as direction
            FROM ACCOUNT_MOVE_LINE A 
            LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
            LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
            LEFT JOIN res_currency D ON A.CURRENCY_ID=D.ID 
            WHERE C.CODE LIKE '"""+subject+"""%' AND B.NAME <> '00000' AND A.DATE >= '"""+ls_startday+"""' AND A.DATE < '"""+date_from+"""'
            GROUP BY quantity, amount_currency,currency_name,direction
        """
        self.env.cr.execute(sql)
        ll_row = self.env.cr.fetchone()
        if(ll_row):
            ls_debit = ll_row[0] or 0.0
            ls_credit = ll_row[1] or 0.0
            ls_quantity = ll_row[2] or 0.0
            ls_amount_currency = ll_row[3] or 0.0
            ls_currency_name = ll_row[4]
        else:
            ls_debit = 0.0
            ls_credit = 0.0
            ls_quantity = 0.0
            ls_amount_currency = 0.0
            ls_currency_name = ''
        if(ls_balance == '1'):
            opening_debit = (float(tmp_debit) + float(ls_debit) - (float(tmp_credit) + float(ls_credit)))
            opening_credit = 0.0
        elif(ls_balance == '2'):
            opening_debit = 0.0
            opening_credit = -(float(tmp_debit) + float(ls_debit) - (float(tmp_credit) + float(ls_credit)))
        else:
            opening_debit = 0.0
            opening_credit = 0.0

        return {'quantity': ls_quantity, 'amount_currency': ls_amount_currency, 'currency_name': ls_currency_name,  'opening_debit': opening_debit, 'opening_credit': opening_credit, 'direction': ls_balance}

    def _get_cur_occurs(self, date_from, date_to, subject):
        # ls_startday = self._get_exactDay("START", date_from)
        # ls_endday = self._get_exactDay("END", date_to)
        sql = """
            SELECT  SUM(A.debit) AS debit,SUM(A.credit) AS credit, SUM(A.quantity) AS quantity, SUM(A.amount_currency) AS amount_currency, D.name as currency_name, (CASE C.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
            FROM ACCOUNT_MOVE_LINE A 
            LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
            LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
            LEFT JOIN res_currency D ON A.CURRENCY_ID=D.ID 
            WHERE C.CODE LIKE '"""+subject+"""%' AND B.NAME <> '00000' AND A.DATE >= '"""+date_from+"""' AND A.DATE <= '"""+date_to+"""'
            GROUP BY currency_name,direction
        """
        self.env.cr.execute(sql)
        ls_row = self.env.cr.fetchone()
        if(ls_row):
            cur_debit = ls_row[0] or 0.0
            cur_credit = ls_row[1] or 0.0
            ls_quantity = ls_row[2] or 0.0
            ls_amount_currency = ls_row[3] or 0.0
            ls_currency_name = ls_row[4]
        else:
            cur_debit = 0.0
            cur_credit = 0.0
            ls_quantity = 0.0
            ls_amount_currency = 0.0
            ls_currency_name = ''

        return {'quantity': ls_quantity, 'amount_currency': ls_amount_currency, 'currency_name': ls_currency_name, 'cur_debit': cur_debit, 'cur_credit': cur_credit}

    def _get_ending_balance(self, open_balance, cur_occurs):
        if(open_balance['direction'] == '1'):
            ending_balance_debit = open_balance['opening_debit'] + cur_occurs['cur_debit'] - (open_balance['opening_credit'] + cur_occurs['cur_credit'])
            ending_balance_credit = 0.0
        elif(open_balance['direction'] == '2'):
            ending_balance_debit = 0.0
            ending_balance_credit = -(open_balance['opening_debit'] + cur_occurs['cur_debit'] - (
                        open_balance['opening_credit'] + cur_occurs['cur_credit']))
        else:
            ending_balance_debit = 0.0
            ending_balance_credit = 0.0
        return {'quantity': cur_occurs['quantity'], 'amount_currency': cur_occurs['amount_currency'], 'currency_name': cur_occurs['currency_name'], 'ending_balance_debit': ending_balance_debit, 'ending_balance_credit': ending_balance_credit}

    def flat_list(self, rlist):
        result = []
        def nested(rlist):
            for i in rlist:
                if isinstance(i, list):
                    nested(i)
                else:
                    result.append(i)
        nested(rlist)
        return result

    # 获取会计区间的开始/结束日期
    def _get_exactDay(self, flag, account_period):
        # 根据会计区间获取准确的日期
        year = account_period[0:4]
        period = account_period[4:6]
        if flag == "START":
            sql = """
                SELECT date_start FROM ps_account_period WHERE year = '"""+year+"""' AND period = '"""+period+"""'
            """
        else:
            sql = """
                SELECT date_end FROM ps_account_period WHERE year = '""" + year + """' AND period = '""" + period + """'
            """
        self.env.cr.execute(sql)
        temp = self.env.cr.fetchone()
        if temp == None:
            raise ValidationError('No period is generated in the fiscal year, please create an accounting period')
        result = temp[0]
        return result


    # 获取所选会计区间的间隔月份
    def month_differ(self, x, y):
        # 根据传入的年、月计算两个日期间隔的月份
        begin_year = int(x[0:4])
        begin_month = int(x[4:6])
        end_year = int(y[0:4])
        end_month = int(y[4:6])
        month_differ = abs((begin_year - end_year) * 12 + (begin_month - end_month) * 1)
        return month_differ + 1

    def padZeroLeft(self, val):
        return '0' + str(val)
