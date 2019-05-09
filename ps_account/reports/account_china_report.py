import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    # TODO saas-17: remove the try/except to directly import from misc
    import xlsxwriter

from odoo import models, api, _
import logging
_logger = logging.getLogger(__name__)

class AccountChinaReport(models.AbstractModel):
    _name = 'account.china.report'
    _inherit = 'account.report'

    filter_style = None  # 表格样式
    filter_account_state = None  # 单据状态
    filter_subject = None  # 科目
    filter_level = None   # 级次
    filter_unit = None    # 往来单位
    filter_partner = None
    filter_auxiliary = None # 辅助核算项

    @api.model
    def _get_options(self, previous_options=None):
        # previous_options = {}
        if not previous_options:
            previous_options = {}
        obj = {}
        if self.filter_subject:
            subjects = self.env['account.account'].search([])
            self.filter_subject_subjectList = [] if self.filter_subject else None
            for item in subjects:
                obj['code'] = item.code
                obj['name'] = item.code + ' ' + item.name
                self.filter_subject_subjectList.append(obj)
                obj = {}
            previous_options["subject_subjectList"] = self.filter_subject_subjectList
        if self.filter_unit:
            units = self.env['res.partner'].search([])
            units = units.sorted(key=lambda r: r.id)
            self.filter_unit_unitList = [] if self.filter_unit else None
            for item in units:
                obj['id'] = item.id
                obj['name'] = item.name
                self.filter_unit_unitList.append(obj)
                obj = {}
            previous_options["unit_unitList"] = self.filter_unit_unitList
        if self.filter_partner:
            partners = self.env['res.partner'].search([])
            partners = partners.sorted(key=lambda r: r.id)
            self.filter_partner_partnerList = [] if self.filter_partner else None
            for item in partners:
                obj['id'] = item.id
                obj['name'] = item.name
                self.filter_partner_partnerList.append(obj)
                obj = {}
            previous_options["partner_partnerList"] = self.filter_partner_partnerList
        return super(AccountChinaReport, self)._get_options(previous_options)

    def get_xlsx(self, options, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        def_style = workbook.add_format({'font_name': 'Arial'})
        title_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'left'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'left': 2, 'right': 2, 'align': 'center', 'valign': 'vcenter'})
        level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
        level_0_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'left'})
        level_0_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'right'})
        ctx = self._set_context(options)
        ctx.update({'no_format':True, 'print_mode':True})
        lines = self.with_context(ctx)._get_lines(options)

        print_id = 0

        if options.get('hierarchy'):
            lines = self.create_hierarchy(lines)

        for line in lines:
            print_id = line['id']
            if line['id'] == 998:
                # 打印科目汇总表
                for y in range(0, len(lines)):
                    sheets = locals()
                    if 'name' in lines[y]:
                        if 'unit' in lines[y]:
                            sheets[y] = workbook.add_worksheet(lines[y]['unit'] + lines[y]['name'])
                            sheets[y].write(0, 0, lines[y]['unit'], title_style_left)
                            sheets[y].write(0, 1, lines[y]['name'], title_style_left)
                        else:
                            sheets[y] = workbook.add_worksheet(lines[y]['name'])
                            sheets[y].write(0, 0, lines[y]['name'], title_style_left)
                    else:
                        sheets[y] = workbook.add_worksheet('sheet' + str(y))
                        sheets[y].write(0, 0, '', title_style_left)
                    sheets[y].set_column(0, 0, 20)
                    x = 0
                    res = self._get_columns_name(options)
                    for column in self._get_columns_name(options):
                        if len(res) == 2:
                            if len(column) == 5:
                                for item in column:
                                    if 'rowspan' in item:
                                        sheets[y].merge_range(1, x, 2, x,item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '), title_style)
                                        x += 1
                                    elif 'colspan' in item:
                                        sheets[y].merge_range(1, x, 1, x + 1,item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '), title_style)
                                        x = x + 2
                            else:
                                w = 0
                                for item in column:
                                    sheets[y].write(0, w,item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),title_style)
                                    w += 1
                            num = 1
                            wid = 8
                        else:
                            sheets[y].write(1, x, column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),title_style)
                            x += 1
                            num = 2
                            wid = len(res)
                    if lines[y].get('level') == 0:
                        style_left = level_0_style_left
                        style_right = level_0_style_right
                        style = level_0_style
                    else:
                        style = def_style
                        style_left = def_style
                        style_right = def_style
                    for x in range(0, wid):
                        for z in range(num, len(lines[y]['columns']) + num):
                            if x == 0:
                                sheets[y].write(z, x, lines[y]['columns'][z - num].get('code'), style_left)
                            if x == 1:
                                sheets[y].write(z, x, lines[y]['columns'][z - num].get('name'), style)
                            if x == 2:
                                sheets[y].write(z, x, lines[y]['columns'][z - num].get('debit'), style_right)
                            if x == 3:
                                sheets[y].write(z, x, lines[y]['columns'][z - num].get('credit'), style_right)

            else:
                for y in range(0, len(lines)):
                    sheets = locals()
                    if 'name' in lines[y]:
                        if 'unit' in lines[y]:
                            sheets[y] = workbook.add_worksheet(lines[y]['unit']+lines[y]['name'])
                            sheets[y].write(0, 0, lines[y]['unit'], title_style_left)
                            sheets[y].write(0, 1, lines[y]['name'], title_style_left)
                        else:
                            sheets[y] = workbook.add_worksheet(lines[y]['name'])
                            sheets[y].write(0, 0, lines[y]['name'], title_style_left)
                    else:
                        sheets[y] = workbook.add_worksheet('sheet'+str(y))
                        sheets[y].write(0, 0, '', title_style_left)
                    sheets[y].set_column(0, 0, 20)
                    x = 0
                    res = self._get_columns_name(options)
                    for column in self._get_columns_name(options):
                        if len(res) == 2:
                            if len(column)==5 :
                                for item in column:
                                    if 'rowspan' in item:
                                        sheets[y].merge_range(1, x, 2, x, item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '), title_style)
                                        x += 1
                                    elif 'colspan' in item:
                                        sheets[y].merge_range(1, x, 1, x+1,item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '), title_style)
                                        x = x + 2
                            else:
                                w = 2
                                for item in column:
                                    sheets[y].write(2, w, item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '), title_style)
                                    w += 1
                            num = 3
                            wid = 8
                        else:
                            sheets[y].write(1, x, column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '), title_style)
                            x += 1
                            num = 2
                            wid = len(res)
                    if lines[y].get('level') == 0:
                        style_left = level_0_style_left
                        style_right = level_0_style_right
                        style = level_0_style
                    else:
                        style = def_style
                        style_left = def_style
                        style_right = def_style

                    for x in range(0, wid):
                        for z in range(num, len(lines[y]['columns'])+num):
                            if wid <= 7:
                                if x == 0:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('date'), style_left)
                                if x == 1:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('name'), style)
                                if x == 2:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('summary'), style_left)
                                if x == 3:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('debit'), style_right)
                                if x == 4:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('credit'), style_right)
                                if x == 5:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('direction'), style)
                                if x == 6:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('f_balance'), style_right)
                            elif wid == 8 and print_id == 999:
                                if x == 0:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('date'), style_left)
                                if x == 1:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('name'), style_left)
                                if x == 2:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('summary'), style_left)
                                if x == 3:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('debit'), style_right)
                                if x == 4:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('credit'), style_right)
                                if x == 5:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('direction'), style)
                                if x == 6:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('balance'), style_right)
                                if x == 7:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('auxiliary'), style)
                            elif wid == 10 and print_id == 999:
                                if x == 0:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('date'), style_left)
                                if x == 1:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('name'), style_left)
                                if x == 2:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('summary'), style_left)
                                if x == 3:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('debit'), style_right)
                                if x == 4:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('credit'), style_right)
                                if x == 5:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('direction'), style)
                                if x == 6:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('balance'), style_right)
                                if x == 7:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('product'), style_left)
                                if x == 8:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('partner'), style_left)
                                if x == 9:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('cashflow'), style_left)
                            elif wid == 8:
                                if x == 0:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('code'), style_left)
                                if x == 1:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('name'), style)
                                if x == 2:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('open_balance_debit'), style_right)
                                if x == 3:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('open_balance_credit'), style_right)
                                if x == 4:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('cur_credit'), style_right)
                                if x == 5:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('cur_debit'), style_right)
                                if x == 6:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('ending_balance_debit'), style_right)
                                if x == 7:
                                    sheets[y].write(z, x, lines[y]['columns'][z - num].get('ending_balance_credit'), style_right)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
