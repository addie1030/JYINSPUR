from odoo import models, fields, api, _
import copy
from odoo.exceptions import ValidationError

class ReportAccountChinaFzyebReport(models.AbstractModel):
    _name = "account.china.fzyeb.report"
    _description = _("浪潮PS辅助余额表")
    _inherit = 'account.china.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

    def _get_columns_name(self, options):
        headers = [[
            {'name': _('Partner '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 16%;background-color:#0073C6;color:white','rowspan':'2'},
            {'name': _('Opening balance'), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 28%;background-color:#0073C6;color:white','colspan':'2'},
            {'name': _(' Current Amount '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 28%;background-color:#0073C6;color:white','colspan':'2'},
            {'name': _(' Final Balance '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 28%;background-color:#0073C6;color:white','colspan':'2'}
            ],
            [
            {'name': _(' Debit '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white '},
            {'name': _(' Credit '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white'},
            {'name': _(' Debit '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white'},
            {'name': _(' Credit '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white'},
            {'name': _(' Debit '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white'},
            {'name': _(' Credit '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 14%;background-color:#0073C6;color:white'}
        ]]
        return headers

    def _get_report_name(self):
        return _("Partner balance sheet")

    def _get_templates(self):
        templates = super(ReportAccountChinaFzyebReport, self)._get_templates()
        templates['main_template'] = 'ps_account.template_fzyeb_reports'
        try:
            self.env['ir.ui.view'].get_view_id('ps_account.template_account_china_fzyeb_line_report')
            templates['line_template'] = 'ps_account.template_account_china_fzyeb_line_report'
            templates['search_template'] = 'ps_account.search_template_china'
        except ValueError:
            pass
        return templates

    @api.model
    def _get_lines(self, options, line_id=None):

        date_from = options.get('date').get('date_from')
        date_to = options.get('date').get('date_to')

        lines = []
        line_num = 1

        sql = """
                SELECT code, name, ps_account_level as level FROM account_account where ps_consider_partner = True
                ORDER BY code
            """
        self.env.cr.execute(sql)
        subjects = self.env.cr.fetchall()

        sql = """
                       SELECT COUNT(*) FROM ACCOUNT_MOVE WHERE DATE >= '"""+date_from+"""' AND DATE <= '"""+date_to+"""'
                    """
        self.env.cr.execute(sql)
        recordCount = self.env.cr.fetchone()[0]

        if recordCount == 0:
            lines.append({
                'id': line_num,
                'name': "",
                'class': '',
                'level': 0,
                'columns': [],
            })
        else:
            for subject in subjects:
                rows = self._get_subject_lines(date_from, date_to, subject)
                lines.append({
                    'id': line_num,
                    'name': _("Subject: ") + subject[0] + " " + subject[1],
                    'class': '',
                    'level': 0,
                    'columns': rows,
                })
        return lines

    def _get_subject_lines(self, date_from, date_to, subject):
        result = []
        sample = {'partner': '', 'open_balance_debit': 0, 'open_balance_credit': 0, 'cur_debit': 0, 'cur_credit': 0, 'ending_balance_debit': 0, 'ending_balance_credit': 0}
        sql = """
                SELECT DISTINCT res_partner.id, res_partner.name FROM account_move_line left join res_partner 
                on account_move_line.partner_id=res_partner.id where account_move_line.partner_id > 0 ORDER BY res_partner.name
            """
        summary = copy.copy(sample)
        summary_open_debit = 0
        summary_open_credit = 0
        summary_cur_debit = 0
        summary_cur_credit = 0
        summary_ending_debit = 0
        summary_ending_credit = 0
        self.env.cr.execute(sql)
        temps = self.env.cr.fetchall()
        for i in range(len(temps)):
            temp = temps[i]
            subject_code = subject[0]
            partner = temp[1]
            level = subject[2]
            item = copy.copy(sample)
            open_balance = self._get_opening_balance(subject_code, date_from, str(temp[0]))
            cur_occurs = self._get_cur_occurs(date_from, date_to, subject_code, str(temp[0]))
            ending_balance = self._get_ending_balance(open_balance, cur_occurs)
            item['partner'] = partner
            item['open_balance_debit'] = round(open_balance['opening_debit'],2)
            item['open_balance_credit'] = round(open_balance['opening_credit'],2)
            item['cur_debit'] = round(cur_occurs['cur_debit'],2)
            item['cur_credit'] = round(cur_occurs['cur_credit'],2)
            item['ending_balance_debit'] = round(ending_balance['ending_balance_debit'],2)
            item['ending_balance_credit'] = round(ending_balance['ending_balance_credit'],2)
            result.append(item)
            if(cur_occurs['cur_debit']==0.0 and cur_occurs['cur_credit']==0.0):
                result.remove(item)
            if(level == 1):
                summary_open_debit += open_balance['opening_debit']
                summary_open_credit += open_balance['opening_credit']
                summary_cur_debit += cur_occurs['cur_debit']
                summary_cur_credit += cur_occurs['cur_credit']
                summary_ending_debit += ending_balance['ending_balance_debit']
                summary_ending_credit += ending_balance['ending_balance_credit']
            # result.reverse()
        summary['partner'] = _('Total')
        summary['open_balance_debit'] = round(summary_open_debit,2)
        summary['open_balance_credit'] = round(summary_open_credit,2)
        summary['cur_debit'] = round(summary_cur_debit,2)
        summary['cur_credit'] = round(summary_cur_credit,2)
        summary['ending_balance_debit'] = round(summary_ending_debit,2)
        summary['ending_balance_credit'] = round(summary_ending_credit,2)
        result.append(summary)
        if (summary_cur_debit == 0.0 and summary_cur_credit == 0.0 and summary_open_debit == 0.0 and summary_open_credit == 0.0):
            result.remove(summary)
        return result

    def _get_opening_balance(self, subject, date_from, temp):
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
        tmp = self.env.cr.fetchone()
        ls_direction = tmp[0]
        sql = """
            SELECT min(B.YEAR) as year
            FROM account_move A
            LEFT JOIN PS_ACCOUNT_PERIOD B ON A.PS_PERIOD_CODE = B.ID
        """
        self.env.cr.execute(sql)
        tmp = self.env.cr.fetchone()
        ls_year = tmp[0]
        if ls_year == None:
            raise ValidationError('No new data for the voucher, please add a new voucher')
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
                LEFT JOIN RES_PARTNER D ON B.PARTNER_ID=D.ID
                LEFT JOIN PS_ACCOUNT_PERIOD E ON B.PS_PERIOD_CODE = E.ID
                WHERE C.CODE LIKE '"""+subject+"""%' AND B.NAME='00000' AND E.YEAR = '"""+str(int(year)+1)+"""'AND A.PARTNER_ID='""" + temp + """'
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
                SELECT SUM(A.debit) AS debit,SUM(A.credit) AS credit,E.YEAR AS ps_period_year,E.PERIOD AS ps_period_code,  C.ps_balance_direction as direction
                FROM ACCOUNT_MOVE_LINE A 
                LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
                LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
                LEFT JOIN RES_PARTNER D ON B.PARTNER_ID=D.ID
                LEFT JOIN PS_ACCOUNT_PERIOD E ON B.PS_PERIOD_CODE = E.ID
                WHERE C.CODE LIKE '""" + subject + """%' AND B.NAME='00000'AND A.PARTNER_ID='""" + temp + """'
                GROUP BY E.YEAR, E.PERIOD, direction
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
            SELECT  SUM(A.debit) AS debit,SUM(A.credit) AS credit,  C.ps_balance_direction as direction
            FROM ACCOUNT_MOVE_LINE A 
            LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
            LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
            LEFT JOIN RES_PARTNER D ON B.PARTNER_ID=D.ID
            WHERE C.CODE LIKE '"""+subject+"""%' AND B.NAME <> '00000' AND A.DATE >= '"""+ls_startday+"""' AND A.DATE < '"""+date_from+"""'AND A.PARTNER_ID='""" + temp + """'
            GROUP BY direction
        """
        self.env.cr.execute(sql)
        ll_row = self.env.cr.fetchone()
        if(ll_row):
            ls_debit = ll_row[0] or 0.0
            ls_credit = ll_row[1] or 0.0
        else:
            ls_debit = 0.0
            ls_credit = 0.0
        if(ls_balance == '1'):
            opening_debit = float(tmp_debit) + float(ls_debit) - (float(tmp_credit) + float(ls_credit))
            opening_credit = 0.0
        elif(ls_balance == '2'):
            opening_debit = 0.0
            opening_credit = -(float(tmp_debit) + float(ls_debit) - (float(tmp_credit) + float(ls_credit)))
        else:
            opening_debit = 0.0
            opening_credit = 0.0

        return {'opening_debit': opening_debit, 'opening_credit': opening_credit, 'direction': ls_balance}

    def _get_cur_occurs(self, date_from, date_to, subject,temp):
        # ls_startday = self._get_exactDay("START", date_from)
        # ls_endday = self._get_exactDay("END", date_to)
        sql = """
            SELECT  SUM(A.debit) AS debit,SUM(A.credit) AS credit, (CASE C.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
            FROM ACCOUNT_MOVE_LINE A 
            LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
            LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
            LEFT JOIN RES_PARTNER D ON B.PARTNER_ID=D.ID
            WHERE C.CODE LIKE '"""+subject+"""%' AND B.NAME <> '00000' AND A.DATE >= '"""+date_from+"""' AND A.DATE <= '"""+date_to+"""'AND A.PARTNER_ID='""" + temp + """'
            GROUP BY direction
        """
        self.env.cr.execute(sql)
        ls_row = self.env.cr.fetchone()
        if(ls_row):
            cur_debit = ls_row[0] or 0.0
            cur_credit = ls_row[1] or 0.0
        else:
            cur_debit = 0.0
            cur_credit = 0.0

        return {'cur_debit': cur_debit, 'cur_credit': cur_credit}

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
        return {'ending_balance_debit': ending_balance_debit, 'ending_balance_credit': ending_balance_credit}

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