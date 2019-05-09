from odoo import models, fields, api, _
import copy
from odoo.exceptions import ValidationError


class ReportAccountChinaTriLedgerReport(models.AbstractModel):
    _name = "account.china.tri.ledger.report"
    _description = _("浪潮PS三栏式明细账")
    _inherit = 'account.china.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_style = {'filter': 'aa'}
    # filter_account_state = [{'id': 'draft', 'name': _('草稿'), 'selected': False},
    #                         {'id': 'checked', 'name': _('已审核'), 'selected': False},
    #                         {'id': 'booked', 'name': _('已记账'), 'selected': False},
    #                         {'id': 'invalid', 'name': _('作废'), 'selected': False}]
    filter_subject = {'subject_from': '1001', 'subject_to': '1001'}

    def _get_columns_name(self, options):
        subject_from = options.get('subject').get('subject_from')
        subject_to = options.get('subject').get('subject_to')
        res = self.env['account.account'].search(['&', ('code', '>=', subject_from), ('code', '<=', subject_to+'zzzzzzzz')])
        if res:
            for n in res:
                if n.ps_consider_product:
                    if n.currency_id:
                        if options.get('style').get('filter') == "cc":
                            headers = [[
                                {'name': _(' Date '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white','rowspan':'2'},
                                {'name': _(' Voucher Number '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white','rowspan':'2'},
                                {'name': _('Abstract'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white','rowspan':'2'},
                                {'name': _(' Debit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white','colspan': '2'},
                                {'name': _(' Credit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white','colspan': '2'},
                                {'name': _(' Direction '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white','rowspan':'2'},
                                {'name': _(' Balance '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white','rowspan':'2'}
                            ],
                            [
                                {'name': _(' Quantity '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white '},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Quantity '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                            ]]
                        if options.get('style').get('filter') == "aa":
                            headers = [
                                {'name': _(' Date '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Voucher Number '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _('Abstract'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                                {'name': _(' Debit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                                {'name': _(' Credit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                                {'name': _(' Direction '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 5%;background-color:#0073C6;color:white'},
                                {'name': _(' Balance '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 15%;background-color:#0073C6;color:white'}
                            ]
                        if options.get('style').get('filter') == "bb":
                            headers = [[
                                {'name': _(' Date '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _(' Voucher Number '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _('Abstract'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _('Currency'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _(' Debit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white',
                                 'colspan': '2'},
                                {'name': _(' Credit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white',
                                 'colspan': '2'},
                                {'name': _(' Direction '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _(' Balance '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                                 'rowspan': '2'}
                            ],
                            [
                                {'name': _(' Foreign Currency '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white '},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Foreign Currency '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                            ]]
                        if options.get('style').get('filter') == "dd":
                            headers = [[
                                {'name': _(' Date '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _(' Voucher Number '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _('Abstract'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 13%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _('Currency'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _(' Debit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 21%;background-color:#0073C6;color:white',
                                 'colspan': '3'},
                                {'name': _(' Credit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 21%;background-color:#0073C6;color:white',
                                 'colspan': '3'},
                                {'name': _(' Direction '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _(' Balance '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                                 'rowspan': '2'}
                            ],
                            [
                                {'name': _(' Quantity '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                                {'name': _(' Foreign Currency '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                                {'name': _(' Quantity '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white '},
                                {'name': _(' Foreign Currency '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 7%;background-color:#0073C6;color:white'},
                            ]]
                    else:
                        if options.get('style').get('filter') == "cc":
                            headers = [[
                                {'name': _(' Date '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white','rowspan':'2'},
                                {'name': _(' Voucher Number '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white','rowspan':'2'},
                                {'name': _('Abstract'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white','rowspan':'2'},
                                {'name': _(' Debit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white','colspan': '2'},
                                {'name': _(' Credit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white','colspan': '2'},
                                {'name': _(' Direction '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white','rowspan':'2'},
                                {'name': _(' Balance '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white','rowspan':'2'}
                            ],
                            [
                                {'name': _(' Quantity '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white '},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Quantity '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                            ]]
                        else:
                            headers = [
                                {'name': _(' Date '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Voucher Number '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _('Abstract'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                                {'name': _(' Debit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                                {'name': _(' Credit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                                {'name': _(' Direction '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 5%;background-color:#0073C6;color:white'},
                                {'name': _(' Balance '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 15%;background-color:#0073C6;color:white'}
                            ]
                else:
                    if n.currency_id:
                        if options.get('style').get('filter') == "bb":
                            headers = [[
                                {'name': _(' Date '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _(' Voucher Number '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _('Abstract'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _('Currency'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _(' Debit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white',
                                 'colspan': '2'},
                                {'name': _(' Credit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 20%;background-color:#0073C6;color:white',
                                 'colspan': '2'},
                                {'name': _(' Direction '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white',
                                 'rowspan': '2'},
                                {'name': _(' Balance '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
                                 'rowspan': '2'}
                            ],
                            [
                                {'name': _(' Foreign Currency '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white '},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Foreign Currency '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Amount '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;width: 10%;background-color:#0073C6;color:white'},
                            ]]
                        else:
                            headers = [
                                {'name': _(' Date '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _(' Voucher Number '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 10%;background-color:#0073C6;color:white'},
                                {'name': _('Abstract'), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                                {'name': _(' Debit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                                {'name': _(' Credit '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                                {'name': _(' Direction '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 5%;background-color:#0073C6;color:white'},
                                {'name': _(' Balance '), 'class': 'string',
                                 'style': 'text-align:center; white-space:nowrap;height:40px;width: 15%;background-color:#0073C6;color:white'}
                            ]
                    else:
                        headers = [
                            {'name': _(' Date '), 'class': 'string',
                             'style': 'text-align:center; white-space:nowrap;height:40px;width: 10%;background-color:#0073C6;color:white'},
                            {'name': _(' Voucher Number '), 'class': 'string',
                             'style': 'text-align:center; white-space:nowrap;height:40px;width: 10%;background-color:#0073C6;color:white'},
                            {'name': _('摘要'), 'class': 'string',
                             'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                            {'name': _(' Debit '), 'class': 'string',
                             'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                            {'name': _(' Credit '), 'class': 'string',
                             'style': 'text-align:center; white-space:nowrap;height:40px;width: 20%;background-color:#0073C6;color:white'},
                            {'name': _(' Direction '), 'class': 'string',
                             'style': 'text-align:center; white-space:nowrap;height:40px;width: 5%;background-color:#0073C6;color:white'},
                            {'name': _(' Balance '), 'class': 'string',
                             'style': 'text-align:center; white-space:nowrap;height:40px;width: 15%;background-color:#0073C6;color:white'}
                        ]
                return headers

    def _get_report_name(self):
        return _("Account ledger")

    # def get_reports_buttons(self):
    #     return [{'name': _('Print Preview'), 'action': 'print_pdf'},
    #             {'name': _('Export (XLSX)'), 'action': 'print_xlsx'}]

    def _get_templates(self):
        templates = super(ReportAccountChinaTriLedgerReport, self)._get_templates()
        templates['main_template'] = 'ps_account.template_tri_ledger_reports'
        try:
            self.env['ir.ui.view'].get_view_id('ps_account.template_account_china_tri_ledger_line_report')
            templates['line_template'] = 'ps_account.template_account_china_tri_ledger_line_report'
            templates['search_template'] = 'ps_account.search_template_china'
        except ValueError:
            pass
        return templates

    @api.model
    def _get_lines(self, options, line_id=None):

        # style = options.get('style').get('filter')
        date_from = options.get('date').get('date_from')
        date_to = options.get('date').get('date_to')
        subject_from = options.get('subject').get('subject_from')
        subject_to = options.get('subject').get('subject_to')
        # account_state = options.get('account_state')

        lines = []
        line_num = 1
        # 获取选定区间所有的科目
        sql = """
            SELECT code, name, ps_consider_product,currency_id FROM account_account where code >= '"""+subject_from+"""' AND code <= '"""+subject_to+'zzzzzzzz'+"""'
            ORDER BY code
        """
        self.env.cr.execute(sql)
        # arr = []
        subjects = self.env.cr.fetchall()
        for subject in subjects:
            if subject[2] and subject[3]:
                if options.get('style').get('filter') == "bb":
                    num1 = False
                    num2 = True
                    num3 = False
                    num4 = False
                elif options.get('style').get('filter') == "cc":
                    num1 = False
                    num2 = False
                    num3 = True
                    num4 = False
                elif options.get('style').get('filter') == "dd":
                    num1 = False
                    num2 = False
                    num3 = False
                    num4 = True
                else:
                    num1 = True
                    num2 = False
                    num3 = False
                    num4 = False
            elif subject[2]:
                if options.get('style').get('filter') == "cc":
                    num1 = False
                    num2 = False
                    num3 = True
                    num4 = False
                else:
                    num1 = True
                    num2 = False
                    num3 = False
                    num4 = False
            elif subject[3]:
                if options.get('style').get('filter') == "bb":
                    num1 = False
                    num2 = True
                    num3 = False
                    num4 = False
                else:
                    num1 = True
                    num2 = False
                    num3 = False
                    num4 = False
            else:
                num1 = True
                num2 = False
                num3 = False
                num4 = False
        sql = """
           SELECT COUNT(*) FROM ACCOUNT_MOVE
        """
        self.env.cr.execute(sql)
        recordCount = self.env.cr.fetchone()[0]

        if len(subjects) <= 0 or recordCount == 0:
            dd = options.get('style').get('filter')
            myoptions = {"subject": {"subject_from": subject[0], "subject_to": subject[0]}, "style": {"filter": dd}}
            headers = self._get_columns_name(myoptions)
            lines.append({
                'id': line_num,
                'name': "",
                'class': '',
                'level': 0,
                'num1': num1,
                'num2': num2,
                'num3': num3,
                'num4': num4,
                'columns': [],
                'headers': headers,
            })
        else:
            for subject in subjects:
                if subject[2] and subject[3]:
                    if options.get('style').get('filter') == "bb":
                        num1 = False
                        num2 = True
                        num3 = False
                        num4 = False
                    elif options.get('style').get('filter') == "cc":
                        num1 = False
                        num2 = False
                        num3 = True
                        num4 = False
                    elif options.get('style').get('filter') == "dd":
                        num1 = False
                        num2 = False
                        num3 = False
                        num4 = True
                    else:
                        num1 = True
                        num2 = False
                        num3 = False
                        num4 = False
                elif subject[2]:
                    if options.get('style').get('filter') == "cc":
                        num1 = False
                        num2 = False
                        num3 = True
                        num4 = False
                    else:
                        num1 = True
                        num2 = False
                        num3 = False
                        num4 = False
                elif subject[3]:
                    if options.get('style').get('filter') == "bb":
                        num1 = False
                        num2 = True
                        num3 = False
                        num4 = False
                    else:
                        num1 = True
                        num2 = False
                        num3 = False
                        num4 = False
                else:
                    num1 = True
                    num2 = False
                    num3 = False
                    num4 = False
                rows = self._get_subject_lines(subject[0], date_from, date_to)
                dd = options.get('style').get('filter')
                myoptions = {"subject": {"subject_from": subject[0], "subject_to": subject[0]}, "style": {"filter": dd}}
                headers = self._get_columns_name(myoptions)
                lines.append({
                    'id': line_num,
                    'name': _("Subject: ") + subject[0] + " " + subject[1],
                    'class': '',
                    'level': 0,
                    'num1': num1,
                    'num2': num2,
                    'num3': num3,
                    'num4': num4,
                    'columns': rows,
                    'headers': headers,
                })
                line_num += 1
        return lines

    def _get_subject_lines(self, subject, date_from, date_to):
        rows = []
        qc = self._get_opening_balance(subject, date_from)
        res = self._get_items(subject, date_from, date_to, qc)
        rows.append(qc)
        for line in res:
            rows.append(line)
        return rows

    def _get_items(self, subject, date_from, date_to, qc):
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
            res = self._get_exactDay1(str(year)+strMonth)
            start = res[0]
            end = res[1]
            sql = """
                SELECT amount_currency,D.name as currency_name,quantity,E.year as ps_period_year,E.period as ps_period_code,hz.name,account.code,account.name AS kmmc,(CASE account.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction,mx.name AS summary,debit,credit,balance,mx.date ,0 AS f_balance 
                FROM account_move_line mx
                LEFT JOIN account_move hz ON mx.move_id=hz.id
                LEFT JOIN account_account account ON mx.account_id=account.id
                LEFT JOIN res_currency D ON mx.currency_id=D.id 
                LEFT  JOIN PS_ACCOUNT_PERIOD E ON hz.PS_PERIOD_CODE = E.ID
                WHERE account.code LIKE '""" + subject + """%' AND HZ.NAME <> '00000' AND mx.date >= '"""+str(start)+"""' AND mx.date <= '"""+str(end)+"""'
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

    # 获取期初余额
    def _get_opening_balance(self, code, date_from):
        #  需要根据科目编号 去找科目ID  再根据科目ID 去找凭证分录 这个麻烦...
        # fiscalyear中state为2的表示已经年结，会在凭证表中新增一条0000的记录，会计区间是下一年的01期
        sql = """
            SELECT (CASE ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
            FROM ACCOUNT_ACCOUNT 
            WHERE code = '""" + code + """'
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
                LEFT  JOIN PS_ACCOUNT_PERIOD D ON B.PS_PERIOD_CODE = D.ID
                WHERE C.CODE LIKE '""" + code + """%' AND B.NAME='00000' AND D.YEAR = '""" + str(int(year) + 1) + """'
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
                SELECT SUM(A.BALANCE)  AS BALANCE,D.YEAR AS ps_period_year,D.PERIOD AS ps_period_code, (CASE C.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
                FROM ACCOUNT_MOVE_LINE A 
                LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
                LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
                LEFT  JOIN PS_ACCOUNT_PERIOD D ON B.PS_PERIOD_CODE = D.ID
                WHERE C.CODE LIKE '""" + code + """%' AND B.NAME='00000'
                GROUP BY D.YEAR, D.PERIOD, direction
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
            SELECT SUM(A.BALANCE)  AS BALANCE,SUM(A.debit) AS debit,SUM(A.credit) AS credit,quantity, amount_currency,D.name as currency_name, (CASE C.ps_balance_direction WHEN '1' THEN '借' WHEN '2' THEN '贷' ELSE '平'END) direction
            FROM ACCOUNT_MOVE_LINE A 
            LEFT JOIN ACCOUNT_MOVE B ON A.MOVE_ID=B.ID 
            LEFT JOIN ACCOUNT_ACCOUNT C ON A.ACCOUNT_ID=C.ID 
            LEFT JOIN res_currency D ON A.CURRENCY_ID=D.ID
            WHERE C.CODE LIKE '""" + code + """%' AND B.NAME <> '00000' AND A.DATE >= '""" + ls_startday + """' AND A.DATE < '""" + date_from + """'
            GROUP BY quantity, amount_currency,currency_name,direction
        """
        self.env.cr.execute(sql)
        ll_row = self.env.cr.fetchone()
        if (ll_row):
            qc = ll_row[0] or 0
            qc_debit = ll_row[1] or 0.0
            qc_credit = ll_row[2] or 0.0
            qc_quantity = ll_row[3] or 0.0
            qc_amount_currency = ll_row[4] or 0.0
            qc_currency_name = ll_row[5]
        else:
            qc = 0
            qc_debit = 0.0
            qc_credit = 0.0
            qc_quantity = 0.0
            qc_amount_currency = 0.0
            qc_currency_name = ''
        qcye = round((float(tmpBalance) + float(qc)),2)
        qcobj = {'direction': ls_direction, 'name': '', 'kmmc': '', 'credit': qc_credit, 'summary': '期初余额',
                 'ps_period_year': '', 'ps_period_code': '', 'balance': 0, 'date': date_from[0:7], 'debit': qc_debit,
                 'code': '', 'f_balance': qcye, 'quantity': qc_quantity, 'amount_currency': qc_amount_currency, 'currency_name': qc_currency_name,}
        return qcobj

    # 获取本月累计
    def _f_currencySum(self, res, prev):
        credit = 0
        debit = 0
        quantity = 0
        amount_currency = 0
        currency_name = ''
        result = []
        periodMonth = copy.copy(res[0])
        periodYear = copy.copy(res[0])
        for item in res:
            item['credit'] = round(float(item['credit']),2)
            item['debit'] = round(float(item['debit']),2)
            if not item['currency_name']:
                item['currency_name'] = ''
            item['currency_name'] = item['currency_name']
            if not item['amount_currency']:
                item['amount_currency'] = 0
            item['amount_currency'] = round(float(item['amount_currency']), 2)
            if not item['quantity']:
                item['quantity'] = 0
            item['quantity'] = round(float(item['quantity']), 2)
            credit += item['credit']
            debit += item['debit']
            amount_currency += item['amount_currency']
            currency_name += item['currency_name']
            quantity += item['quantity']
            item['f_balance'] = round(float(prev['f_balance'] + debit - credit),2)  # 计算每一条分录的余额
            result.append(item)  # 把计算过余额的分录添加到新数组中
        balance = prev['f_balance'] + debit - credit
        periodMonth['date'] = str(periodMonth['date'])[0:7]  # 本期日期格式化
        periodMonth['name'] = ''
        periodMonth['credit'] = round(float(credit),2)
        periodMonth['debit'] = round(float(debit),2)
        periodMonth['quantity'] = round(float(quantity), 2)
        periodMonth['currency_name'] = currency_name
        periodMonth['amount_currency'] = round(float(amount_currency), 2)
        periodMonth['summary'] = _('Total in this period')
        periodMonth['f_balance'] = round(float(balance),2)
        periodYear['date'] = str(periodYear['date'])[0:7]
        periodYear['name'] = ''
        periodYear['summary'] = _('Total accumulation this year')
        periodYear['credit'] = round(float(credit + prev['credit']),2)
        periodYear['debit'] = round(float(debit + prev['debit']),2)
        periodYear['quantity'] = round(float(quantity + prev['quantity']), 2)
        periodYear['currency_name'] = currency_name
        periodYear['amount_currency'] = round(float(amount_currency + prev['amount_currency']), 2)
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
                SELECT date_start FROM ps_account_period WHERE year = '""" + year + """' AND period = '""" + period + """'
            """
        else:
            sql = """
                SELECT date_end FROM ps_account_period WHERE year = '""" + year + """' AND period = '""" + period + """'
            """
        self.env.cr.execute(sql)
        temp = self.env.cr.fetchone()
        if temp == None:
            raise ValidationError(_('No period is generated in the fiscal year, please create an accounting period'))
        result = temp[0]
        return result

        # 怎样汇总本期合计，本年累计？
        # 汇总完之后怎样插入到本期后面

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

    @api.model
    def tri_ledger_link(self, date, name):
        obj = self.env['account.move'].search([('date', '=', date), ('name', '=', name)])
        link_id = obj.id
        form_view_id = self.env.ref('ps_account.view_move_form_new').id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'target': 'current',
            'res_id': link_id,
            'views': [[form_view_id, 'form']],
            'context': {
                'search_default_misc_filter': 1,
                'view_no_maturity': 1,
                'manual_move': '1'
            }
        }

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
            raise ValidationError(_('No period is generated in the fiscal year, please create an accounting period'))
        result = [temp[0],temp[1]]
        return result

