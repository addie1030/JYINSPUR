from odoo import models, fields, api, _
import copy
from odoo.exceptions import ValidationError


class ReportAccountChinaAuxiliaryDetailReport(models.AbstractModel):
    _name = "account.china.auxiliary.detail.report"
    _description = _("浪潮PS辅助总账查询")
    _inherit = 'account.china.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

    def _get_columns_name(self, options):
        headers = [
            {'name': _(' Date '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white'},
            {'name': _(' Voucher Number '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _('Abstract'), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 25%;background-color:#0073C6;color:white'},
            {'name': _(' Debit '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 18%;background-color:#0073C6;color:white'},
            {'name': _(' Credit '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 18%;background-color:#0073C6;color:white'},
            {'name': _(' Direction '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Balance '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 19%;background-color:#0073C6;color:white'}
        ]
        return headers

    def _get_report_name(self):
        return _("Partner Detail Ledger")

    def _get_templates(self):
        templates = super(ReportAccountChinaAuxiliaryDetailReport, self)._get_templates()
        templates['main_template'] = 'ps_account.template_detail_reports'
        try:
            self.env['ir.ui.view'].get_view_id('ps_account.template_account_china_detail_line_report')
            templates['line_template'] = 'ps_account.template_account_china_detail_line_report'
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
        # 获取选定区间所有的科目
        sql = """
            SELECT code, name FROM account_account where ps_consider_partner = True
            ORDER BY code
        """
        self.env.cr.execute(sql)
        subjects = self.env.cr.fetchall()

        sql = """
            SELECT id, name FROM res_partner 
            ORDER BY id
        """
        self.env.cr.execute(sql)
        units = self.env.cr.fetchall()

        sql = """
           SELECT COUNT(*) FROM ACCOUNT_MOVE  WHERE DATE >= '"""+date_from+"""' AND DATE <= '"""+date_to+"""'
        """
        self.env.cr.execute(sql)
        recordCount = self.env.cr.fetchone()[0]

        if len(subjects) <= 0 or recordCount == 0:
            lines.append({
                'id': line_num,
                'unit': '',
                'name': "",
                'class': '',
                'level': 0,
                'columns': [],
            })
        else:
            for unit in units:
                for subject in subjects:
                    rows = self._get_row(subject[0], date_from, date_to, str(unit[0]))
                    if len(rows) == 1:
                        continue
                    lines.append({
                        'id': line_num,
                        'unit': _('Exchange Unit: ') + unit[1],
                        'name': _("Subject: ") + subject[0] + " " + subject[1],
                        'class': '',
                        'level': 0,
                        'columns': rows,
                    })
                    line_num += 1
        return lines

    def _get_row(self, subject, date_from, date_to, unit):
        rows = []
        qc = self._get_opening_balance(subject, date_from, unit)
        res = self._get_items(subject, date_from, date_to, qc, unit)
        rows.append(qc)
        for line in res:
            rows.append(line)
        return rows

    def _get_opening_balance(self, code, date_from, unit):
        #  需要根据科目编号 去找科目ID  再根据科目ID 去找凭证分录 这个麻烦...
        # fiscalyear中state为2的表示已经年结，会在凭证表中新增一条0000的记录，会计区间是下一年的01期
        sql = """
            SELECT (CASE ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
            FROM ACCOUNT_ACCOUNT 
            WHERE code = '""" + code + """'
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
        tmp = self.env.cr.fetchone()
        ls_year = tmp[0]
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
        if (year):
            #  如果存在年结，去找生成的下一年的期初凭证
            sql = """
                SELECT SUM(A.BALANCE) AS BALANCE,A.DATE AS vsdate, (CASE C.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
                FROM ACCOUNT_MOVE_LINE A 
                LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
                LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
                LEFT JOIN RES_PARTNER D ON B.PARTNER_ID = D.ID
                LEFT JOIN PS_ACCOUNT_PERIOD E ON B.PS_PERIOD_CODE = E.ID
                WHERE C.CODE LIKE '""" + code + """%' AND B.NAME='00000' AND E.YEAR = '""" + str(int(year) + 1) + """' AND B.PARTNER_ID = '""" + unit + """'
                GROUP BY vsdate, direction
            """
            self.env.cr.execute(sql)
            ls_row = self.env.cr.fetchone()
            tmpBalance = ls_row[0]
            # 找那一期的开始日期
            ls_startday = str(self._get_exactDay("START", (str(year) + '01')))
            # ls_direction = ls_row[2]
        else:
            sql = """
                SELECT SUM(A.BALANCE)  AS BALANCE,E.YEAR AS ps_period_year,E.PERIOD AS ps_period_code, (CASE C.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
                FROM ACCOUNT_MOVE_LINE A 
                LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
                LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
                LEFT JOIN RES_PARTNER D ON B.PARTNER_ID = D.ID
                LEFT JOIN PS_ACCOUNT_PERIOD E ON B.PS_PERIOD_CODE = E.ID
                WHERE C.CODE LIKE '""" + code + """%' AND B.NAME='00000'  AND B.PARTNER_ID = '""" + unit + """'
                GROUP BY E.YEAR, E.PERIOD, direction
            """
            self.env.cr.execute(sql)
            row = self.env.cr.fetchone()
            if (row):
                tmpBalance = row[0] or 0
                ls_startday = str(self._get_exactDay("START", (str(row[1]) + str(row[2]))))
            else:
                tmpBalance = 0
                ls_startday = str(self._get_exactDay("START", (str(ls_year) + str(ls_month))))
            # ls_direction = row[3]
        sql = """
            SELECT SUM(A.BALANCE)  AS BALANCE, (CASE C.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
            FROM ACCOUNT_MOVE_LINE A 
            LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
            LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
            LEFT JOIN RES_PARTNER D ON B.PARTNER_ID = D.ID
            WHERE C.CODE LIKE '""" + code + """%' AND B.NAME <> '00000' AND A.DATE >= '""" + ls_startday + """' AND A.DATE < '""" + date_from + """'  AND B.PARTNER_ID = '""" + unit + """'
            GROUP BY direction
        """
        self.env.cr.execute(sql)
        ll_row = self.env.cr.fetchone()
        if (ll_row):
            qc = ll_row[0] or 0
        else:
            qc = 0
        qcye = round((float(tmpBalance) + float(qc)),2)
        qcobj = {'direction': ls_direction, 'name': '', 'kmmc': '', 'credit': 0, 'summary': '期初余额',
                 'ps_period_year': '', 'ps_period_code': '', 'balance': 0, 'date': date_from[0:7], 'debit': 0,
                 'code': '', 'f_balance': qcye}
        return qcobj

    def _get_items(self, subject, date_from, date_to, qc, unit):
        month_diff = self.month_differ(date_from, date_to)
        year = int(date_from[0:4])
        month = int(date_from[5:7])
        result = []
        # 期初余额
        last_sum = copy.copy(qc)
        if month_diff <= 0:
            month_diff = 1
            # for index in range(len(vals)):
            #     vals[index-1]['Year'] = vals[index-1]['date'].split("-")[0]
            #     vals[index - 1]['Month'] = vals[index - 1]['date'].split("-")[1]
            #     vals[index - 1]['Day'] = vals[index - 1]['date'].split("-")[2]
            # return vals
        for i in range(month_diff):
            if len(str(month)) == 1:
                strMonth = self.padZeroLeft(month)
            else:
                strMonth = str(month)
            # 强数据类型的就是不好  什么都得自己转···
            res = self._get_exactDay1(str(year) + strMonth)
            start = res[0]
            end = res[1]
            sql = """
                SELECT E.YEAR AS ps_period_year,E.PERIOD AS ps_period_code,hz.name,account.code,account.name AS kmmc,(CASE account.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction,mx.name AS summary,debit,credit,balance,mx.date ,0 AS f_balance 
                FROM account_move_line mx
                LEFT JOIN account_move hz ON mx.move_id=hz.id
                LEFT JOIN account_account account ON mx.account_id=account.id
                LEFT JOIN RES_PARTNER D ON hz.PARTNER_ID = D.ID
                LEFT JOIN PS_ACCOUNT_PERIOD E ON hz.PS_PERIOD_CODE = E.ID
                WHERE account.code LIKE '""" + subject + """%' AND HZ.NAME <> '00000' AND mx.date >= '"""+str(start)+"""' AND mx.date <= '"""+str(end)+"""' AND hz.PARTNER_ID = '""" + unit + """'
                ORDER BY date,balance,direction
            """
            self.env.cr.execute(sql)
            res = self.env.cr.dictfetchall()
            if len(res) > 0:
                ret = self._f_currencySum(res, last_sum)
                last_sum = ret[-1]
                result.append(ret)
            month += 1
            if (month > 12):
                year += 1
                month = 1
        # 判断列表是否为空  再把不为空的列表扁平化一下
        return self.flat_list(result) if len(result) > 0 else []

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

    def _f_currencySum(self, res, prev):
        credit = 0
        debit = 0
        result = []
        periodMonth = copy.copy(res[0])
        periodYear = copy.copy(res[0])
        for item in res:
            item['credit'] = round(float(item['credit']), 2)
            item['debit'] = round(float(item['debit']), 2)
            credit += item['credit']
            debit += item['debit']
            item['f_balance'] = round(float(prev['f_balance'] + debit - credit), 2)  # 计算每一条分录的余额
            result.append(item)  # 把计算过余额的分录添加到新数组中
        balance = prev['f_balance'] + debit - credit
        periodMonth['date'] = str(periodMonth['date'])[0:7]  # 本期日期格式化
        periodMonth['name'] = ''
        periodMonth['credit'] = round(float(credit),2)
        periodMonth['debit'] = round(float(debit),2)
        periodMonth['summary'] = _('Total in this period')
        periodMonth['f_balance'] = round(float(balance),2)
        periodYear['date'] = str(periodYear['date'])[0:7]
        periodYear['name'] = ''
        periodYear['summary'] = _('Total accumulation this year')
        periodYear['credit'] = round(float(credit + prev['credit']),2)
        periodYear['debit'] = round(float(debit + prev['debit']),2)
        periodYear['f_balance'] = round(float(balance),2)
        result.append(periodMonth)
        result.append(periodYear)
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
        begin_month = int(x[5:7])
        end_year = int(y[0:4])
        end_month = int(y[5:7])
        month_differ = abs((begin_year - end_year) * 12 + (begin_month - end_month) * 1)
        return month_differ + 1

    def padZeroLeft(self, val):
        return '0' + str(val)

    def _get_exactDay1(self, date):
        # 根据会计区间获取准确的日期
        year = date[0:4]
        month = date[4:6]
        ps_date = year + '-' + month + '-01'
        sql = """
                        SELECT date_start,date_end FROM ps_account_period WHERE date_start = '""" + ps_date + """'
                    """
        self.env.cr.execute(sql)
        temp = self.env.cr.fetchone()
        if temp == None:
            raise ValidationError('No period is generated in the fiscal year, please create an accounting period')
        result = [temp[0],temp[1]]
        return result