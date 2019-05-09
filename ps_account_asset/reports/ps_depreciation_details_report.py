from odoo import models, api, _
from odoo.tools.float_utils import float_round
import logging

import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)

class PsDepreciationDetailsReport(models.AbstractModel):
    _name = "ps.depreciation.details.report"
    _description = _("Depreciation Details Report")
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_account_analytic = {'account_analytic_from': '1'}
    filter_asset_type = {'asset_type_from': '1'}
    
    @api.model
    def _get_options(self, previous_options=None):
        """
        前后端参数交互
        :param previous_options:
        """
        if not previous_options:
            previous_options = {}
        obj = {}
        if self.filter_account_analytic:
            departments = self.env['ps.asset.department'].search([])
            account_analytics = self.env['account.analytic.account'].search([('id','in',[x.ps_analytic_id.id for x in departments])])
            account_analytics = account_analytics.sorted(key=lambda r: r.id)
            self.filter_account_analyticList = [] if self.filter_account_analytic else None
            for item in account_analytics:
                obj['id'] = item.id
                obj['name'] = item.name
                self.filter_account_analyticList.append(obj)
                obj = {}
            obj['id'] = '0'
            obj['name'] = _('All Departments')
            self.filter_account_analyticList.insert(0,obj)
            obj = {}
            previous_options["account_analyticList"] = self.filter_account_analyticList
        if self.filter_asset_type:
            account_types = self.env['account.asset.category'].search([])
            account_types = account_types.sorted(key=lambda r: r.id)
            self.filter_asset_typeList = [] if self.filter_asset_type else None
            for item in account_types:
                obj['id'] = item.id
                obj['name'] = item.name
                self.filter_asset_typeList.append(obj)
                obj = {}
            obj['id'] = '0'
            obj['name'] = _('All Types')
            self.filter_asset_typeList.insert(0,obj)
            obj = {}
            previous_options["asset_typeList"] = self.filter_asset_typeList
        return super(PsDepreciationDetailsReport, self)._get_options(previous_options)

    def _get_columns_name(self, options):
        """
        列名
        :param options:
        :return: column_names
        """
        headers = [
            {'name': _(' Asset Category '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white'},
            {'name': _(' Department '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Asset Code '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Asset '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Depreciation Date '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Depreciation '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Cumulative Depreciation '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Asset Value '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Residual Value '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            ]
        return headers
    
    def _get_report_name(self):
        """
        报表名称
        """
        return _("Depreciation details report")

    def _get_templates(self):
        """
        模板调用
        :return: templates
        """
        templates = super(PsDepreciationDetailsReport, self)._get_templates()
        templates['main_template'] = 'ps_account_asset.template_depreciation_details_report'
        try:
            self.env['ir.ui.view'].get_view_id('ps_account_asset.template_depreciation_details_line_report')
            templates['line_template'] = 'ps_account_asset.template_depreciation_details_line_report'
            templates['search_template'] = 'ps_account_asset.search_template_asset'
        except ValueError:
            pass
        return templates

    @api.model
    def _get_lines(self, options, line_id=None):
        """
        获取明细行数据
        :param options:
        :param line_id:
        :return: line_values
        """
        date_from = options.get('date').get('date_from')
        date_to = options.get('date').get('date_to')
        account_analytic_from = options.get('account_analytic').get('account_analytic_from')
        if options.get('account_analytic').get('account_analytic_from') == '0':
            is_all_analytic = True
        else:
            is_all_analytic = False
        asset_type_from = options.get('asset_type').get('asset_type_from')
        if options.get('asset_type').get('asset_type_from') == '0':
            is_all_type = True
        else:
            is_all_type = False
        lines = []
        rows = []
        sql = """\
                SELECT aadl.asset_id,aadl.depreciation_date,aal.amount,aal.name,aadl.id
                FROM account_analytic_line aal
                LEFT JOIN account_move_line aml ON aal.move_id = aml.id
                LEFT JOIN account_move am ON am.id = aml.move_id
                LEFT JOIN account_asset_depreciation_line aadl ON aadl.move_id = am.id
                LEFT JOIN account_asset_asset aaa ON aadl.asset_id = aaa.id
                LEFT JOIN account_asset_category aac ON aac.id = aaa.category_id
                WHERE CASE WHEN %s THEN 1=1
                ELSE aal.account_id = %s END
                AND CASE WHEN %s THEN 1=1
                ELSE aac.id = %s END
                AND aadl.depreciation_date >= cast(\'%s\' as date)
                AND aadl.depreciation_date <= cast(\'%s\' as date)
                ORDER BY aal.name,aadl.depreciation_date
        """%(is_all_analytic,account_analytic_from, is_all_type, asset_type_from, date_from, date_to)
        self.env.cr.execute(sql)
        depreciations = self.env.cr.fetchall()
        # dict_departments={}
        precision = self.env['decimal.precision'].precision_get('Product Price')
        # for dep in depreciations:
        #     if dict_departments.__contains__(dep[3]):
        #         temp_value = dict_departments.pop(dep[3])
        #         dict_departments.setdefault(dep[3], round(dep[2],precision) + temp_value)
        #     else:
        #         dict_departments.setdefault(dep[3], round(dep[2],precision))
        for dep in depreciations:
            asset = self.env['account.asset.asset'].search([('id','=',dep[0])])
            depreciation_line = self.env['account.asset.depreciation.line'].search([('id','=',dep[4])])
            dict_departments = {}
            for dep_son in depreciations:
                if dep_son[1] <= depreciation_line.depreciation_date:
                    if dict_departments.__contains__(dep_son[3]):
                        temp_value = dict_departments.pop(dep_son[3])
                        dict_departments.setdefault(dep_son[3], round(dep_son[2], precision) + temp_value)
                    else:
                        dict_departments.setdefault(dep_son[3], round(dep_son[2], precision))
            rows.append({
                'Asset Category': asset.category_id.name,
                'Department': dep[3],
                'Asset Code': asset.code,
                'Asset': asset.name,
                'Depreciation Date': depreciation_line.depreciation_date,
                'Depreciation': round(dep[2], precision),
                'Cumulative Depreciation': dict_departments.get(dep[3], round(dep[2],precision)),
                'Asset Value': asset.value,
                'Residual Value': asset.value_residual,
            })
        line_num = 1
        lines.append({
            'id': line_num,
            'unit': _('Exchange Unit: ') + str(line_num),
            'name': '',
            'class': '',
            'level': 0,
            'columns': rows,
        })
        line_num += 1
        return lines
    
    def get_xlsx(self, options, response):
        """
        导出报表
        :param options:
        :param response:
        """
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
        for line in lines:
            print_id = line['id']
            for y in range(0, len(lines)):
                sheets = locals()
                sheets[y] = workbook.add_worksheet('sheet' + str(y))
                for index,column in enumerate(self._get_columns_name(options)):
                    sheets[y].set_column(0, index, len(column.get('name')))
                x = 0
                res = self._get_columns_name(options)
                for column in self._get_columns_name(options):
                    if len(res) == 2:
                        if len(column) == 5:
                            for item in column:
                                if 'rowspan' in item:
                                    sheets[y].merge_range(1, x, 2, x,
                                                          item.get('name', '').replace('<br/>', ' ').replace('&nbsp;',
                                                                                                             ' '),
                                                          title_style)
                                    x += 1
                                elif 'colspan' in item:
                                    sheets[y].merge_range(1, x, 1, x + 1,
                                                          item.get('name', '').replace('<br/>', ' ').replace('&nbsp;',
                                                                                                             ' '),
                                                          title_style)
                                    x = x + 2
                        else:
                            w = 0
                            for item in column:
                                sheets[y].write(0, w, item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),
                                                title_style)
                                w += 1
                        num = 1
                        wid = 8
                    else:
                        sheets[y].write(1, x, column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),
                                        title_style)
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
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Asset Category'), style_left)
                        if x == 1:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Department'), style_left)
                        if x == 2:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Asset Code') if lines[y]['columns'][z - num].get('Asset Code') else '', style_left)
                        if x == 3:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Asset'), style_left)
                        if x == 4:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Depreciation Date').strftime('%Y-%m-%d'), style_right)
                        if x == 5:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Depreciation'), style_right)
                        if x == 6:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Cumulative Depreciation'), style_right)
                        if x == 7:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Asset Value'), style_right)
                        if x == 8:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Residual Value'), style_right)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
