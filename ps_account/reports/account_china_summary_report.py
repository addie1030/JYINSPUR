from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class ReportAccountChinaSummaryReport(models.AbstractModel):
    _name = "account.china.summary.report"
    _description = _("SAP PS Subjects Summary")
    _inherit = 'account.china.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}

    def _get_columns_name(self, options):

        date_from = options['date']['date_from']
        date_to = options['date']['date_to']

        if date_from > date_to:
            raise ValidationError(_('The start time should not be greater than the end time.'))

        date_count = len(self.env['account.move'].search([('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'posted')]))
        headers = [[
            {
                'name': _(' Certificate number: ') + str(date_count) + _(' Page') if date_count else _(' Certificate number: 0 Page'),
                'class': 'string',
                'style': 'text-align:right; white-space:nowrap; background-color:#F9F9F9; color:black; font-weigth:normal',
                'rowspan': '1',
                'colspan': '4'
            }
        ],
        [
            {
                'name': _(' Subject Number '), 'class': 'string',
                'style': 'text-align:center; white-space:nowrap; width:25%; background-color:#F2F2F2; color:black',
                'rowspan': '1',
                'colspan': '1'
            },
            {
                'name': _(' Subject Name '), 'class': 'string',
                'style': 'text-align:center; white-space:nowrap; width:25%; background-color:#F2F2F2; color:black',
                'rowspan': '1',
                'colspan': '1'
            },
            {
                'name': _(' Debit amount '), 'class': 'string',
                'style': 'text-align:center; white-space:nowrap; width:25%; background-color:#F2F2F2; color:black',
                'rowspan': '1',
                'colspan': '1'
            },
            {
                'name': _(' Crebit amount '), 'class': 'string',
                'style': 'text-align:center; white-space:nowrap; width:25%; background-color:#F2F2F2; color:black',
                'rowspan': '1',
                'colspan': '1'
            }
        ]]
        return headers


    def _get_report_name(self):
        return _("Account summary account")


    def _get_templates(self):
        templates = super(ReportAccountChinaSummaryReport, self)._get_templates()
        templates['main_template'] = 'ps_account.template_summary_reports'
        try:
            self.env['ir.ui.view'].get_view_id('ps_account.template_account_china_summary_line_report')
            templates['line_template'] = 'ps_account.template_account_china_summary_line_report'
            templates['search_template'] = 'ps_account.search_template_china'
        except ValueError:
            pass
        return templates


    @api.model
    def _get_lines(self, options, line_id=None):

        date_from = options['date']['date_from']
        date_to = options['date']['date_to']

        lines_all = []

        sql = """
           SELECT COUNT(*) FROM ACCOUNT_MOVE
        """
        self.env.cr.execute(sql)
        recordCount = self.env.cr.fetchone()[0]

        if recordCount == 0:
            lines_all.append({
                'id': 998,
                'name':'',
                'class': '',
                'columns': [],
            })
            return lines_all

        rows = self._get_row(date_from, date_to)
        lines_all.append({
            'id': 998,
            'name':'',
            'class': '',
            'columns': rows,
        })

        return lines_all


    def _get_row(self, date_from, date_to):

        # 搜索每一行的数据
        sql_line = """
                    SELECT 
                        b.code, b.name, sum(a.debit) debit, sum(a.credit) credit, b.account_attribute_id
                    FROM 
                        account_move_line as a,
                        account_account as b,
                        account_move as c
                    WHERE
                        a.account_id = b.id and
                        c.company_id = """ + str(self.env.user.company_id.id) + """ and
                        c.state = 'posted' and
                        c.id = a.move_id and
                        c.date <= '""" + date_to + """' and
                        c.date >= '""" + date_from + """'
                    GROUP BY
                        b.code, b.name, b.account_attribute_id
                    ORDER BY
                        b.account_attribute_id
                """

        # 搜索每一组的各行加和数据
        sql_sum = """
                    SELECT
                        sum(debit) debit, sum(credit) credit, p.account_attribute_id
                    FROM (
                        SELECT
                            sum(a.debit) debit, sum(a.credit) credit, b.account_attribute_id
                        FROM
                            account_move_line as a,
                            account_account as b,
                            account_move as c
                        WHERE
                            a.account_id = b.id and
                            c.state = 'posted' and
                            c.company_id = """ + str(self.env.user.company_id.id) + """ and
                            c.id = a.move_id and
                            c.date <= '""" + date_to + """' and
                            c.date >= '""" + date_from + """'
                        GROUP BY
                            b.account_attribute_id
                        ORDER BY
                            b.account_attribute_id
                    ) as p
                    GROUP BY
                        p.account_attribute_id
                """

        # 搜索所有的合计
        sql_sum_all = """
                    SELECT sum(p.debit), sum(p.credit)
                    FROM (
                        SELECT
                            sum(a.debit) debit, sum(a.credit) credit, b.account_attribute_id
                        FROM
                            account_move_line as a,
                            account_account as b,
                            account_move as c
                        WHERE
                            a.account_id = b.id and
                            c.state = 'posted' and
                            c.company_id = """ + str(self.env.user.company_id.id) + """ and
                            c.id = a.move_id and
                            c.date <= '""" + date_to + """' and
                            c.date >= '""" + date_from + """'
                        GROUP BY
                            b.account_attribute_id
                        ORDER BY
                            b.account_attribute_id
                    ) as p
                """

        # 搜索小计分类
        sql_attribute = """
                    SELECT id, name
                    FROM ps_account_account_attribute
                """

        self.env.cr.execute(sql_line)
        subjects_all = self.env.cr.fetchall() # 获取所有已过账凭证数据

        self.env.cr.execute(sql_sum)
        subjects_sum = self.env.cr.fetchall() # 获取所有已过账凭证数据的分类总和

        self.env.cr.execute(sql_sum_all)
        subjects_sum_all = self.env.cr.fetchall() # 获取所有已过账凭证数据的总和

        self.env.cr.execute(sql_attribute)
        subjects_attribute = self.env.cr.fetchall() # 获取所有分类记录

        lines_all = []
        lines_sum = {}
        lines_attribute = {}
        line_attribute = 1
        none_attribute = 0  # 未分类ID

        for subject in subjects_sum:
            # 组织获取到的 分类总和 数据
            lines_sum[subject[2]] = {'debit': subject[0], 'credit': subject[1]}

        for subject in subjects_attribute:
            # 定义一个none_attribute字段，用于未定义字段的使用
            lines_attribute[subject[0]] = subject[1]
            if int(subject[0]) > none_attribute:
                none_attribute = int(subject[0])

        for index, subject in enumerate(subjects_all):
            # 如果获取到的所有凭证数据中有未定义分类None，则添加未定义分类，并将未定义分类定未其余已定义分类的最大的一个+1
            if subject[4] is None:
                lines_attribute[none_attribute + 1] = _('Unclassified')
            if subject[4] is None:
                attribute = none_attribute + 1
            else:
                attribute = subject[4]
            if index == 0:
                line_attribute = attribute

            if line_attribute != attribute:
                # 进行凭证数据展示时，如果凭证数据的分类发生变化（如：1类添加完毕，开始添加2类时），则先添加对应分类的凭证分类总和数据
                attribute_name = ""
                if lines_attribute[line_attribute] == 'assets':
                    attribute_name = _('assets')
                if lines_attribute[line_attribute] == 'Liabilities':
                    attribute_name = _('Liabilities')
                if lines_attribute[line_attribute] == 'Equity':
                    attribute_name = _('Equity')
                if lines_attribute[line_attribute] == 'cost':
                    attribute_name = _('cost')
                if lines_attribute[line_attribute] == 'profit and loss':
                    attribute_name = _('profit and loss')

                lines_all.append({
                    'code': attribute_name + _(' Subtotal'),
                    'name': '',
                    'debit': format(lines_sum[line_attribute]['debit'], '0,.2f') if lines_sum[line_attribute]['debit'] else '',
                    'credit': format(lines_sum[line_attribute]['credit'], '0,.2f') if lines_sum[line_attribute]['credit'] else '',
                    'subtotal': True,  # 是否为小计与合计行
                })
                line_attribute = attribute

            lines_all.append({
                'code': subject[0],
                'name': subject[1],
                'debit': format(subject[2], '0,.2f') if subject[2] else '',
                'credit': format(subject[3], '0,.2f') if subject[3] else '',
                'subtotal': False,
            })

            if index == len(subjects_all) - 1:
                attribute_name = ""
                if lines_attribute[attribute] == 'assets':
                    attribute_name = _('assets')
                if lines_attribute[attribute] == 'Liabilities':
                    attribute_name = _('Liabilities')
                if lines_attribute[attribute] == 'Equity':
                    attribute_name = _('Equity')
                if lines_attribute[attribute] == 'cost':
                    attribute_name = _('cost')
                if lines_attribute[attribute] == 'profit and loss':
                    attribute_name = _('profit and loss')
                if subject[4]:
                    lines_all.append({
                        'code': attribute_name + _(' Subtotal'),
                        'name': '',
                        'debit': format(lines_sum[attribute]['debit'], '0,.2f') if lines_sum[attribute]['debit'] else '',
                        'credit': format(lines_sum[attribute]['credit'], '0,.2f') if lines_sum[attribute]['credit'] else '',
                        'subtotal': True,
                    })
                else:
                    lines_all.append({
                        'code': _('Unclassified Subtotal'),
                        'name': '',
                        'debit': format(lines_sum[subject[4]]['debit'], '0,.2f') if lines_sum[subject[4]]['debit'] else '',
                        'credit': format(lines_sum[subject[4]]['credit'], '0,.2f') if lines_sum[subject[4]]['credit'] else '',
                        'subtotal': True,
                    })
                lines_all.append({
                    'code': _('Total'),
                    'name': '',
                    'debit': format(subjects_sum_all[0][0], '0,.2f') if subjects_sum_all[0][0] else '',
                    'credit': format(subjects_sum_all[0][1], '0,.2f') if subjects_sum_all[0][1] else '',
                    'subtotal': True,
                })

        return lines_all
