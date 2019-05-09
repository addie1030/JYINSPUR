from odoo import models, api, _
from odoo.tools.float_utils import float_round
import logging

import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)


class PsAssetAnalysisReport(models.AbstractModel):
    _name = "ps.asset.analysis.report"
    _description = _("Asset Analysis Report")
    _inherit = 'account.report'
    
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_analytic_increase_style = {'analytic_increase_style_para': '1'}
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
        if self.filter_analytic_increase_style:
            change_models = self.env['ps.asset.change.mode'].search([])
            change_list = []
            for change_model in change_models:
                change_list.append(change_model.category)
                change_list = list(set(change_list))
            self.filter_analytic_increaseList = [] if self.filter_analytic_increase_style else None
            obj['key'] = 'reduce'
            obj['name'] = _(' Reduce')
            self.filter_analytic_increaseList.append(obj)
            obj = {}
            obj['key'] = 'add'
            obj['name'] = _(' Add')
            self.filter_analytic_increaseList.append(obj)
            obj = {}
            obj['key'] = '0'
            obj['name'] = _('All Types')
            self.filter_analytic_increaseList.insert(0, obj)
            obj = {}
            previous_options["analytic_increaseList"] = self.filter_analytic_increaseList
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
            self.filter_asset_typeList.insert(0, obj)
            obj = {}
            previous_options["asset_typeList"] = self.filter_asset_typeList
        return super(PsAssetAnalysisReport, self)._get_options(previous_options)
    
    def _get_columns_name(self, options):
        """
        列名
        :param options:
        :return: column_names
        """
        headers = [
            {'name': _(' Increase Or Decrease '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white'},
            {'name': _(' Asset Category '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Asset Code '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Asset '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Former Quantity '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Latter Quantity '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Former Value '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Latter Value '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Former Accumulated Depreciation '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
            {'name': _(' Latter Accumulated Depreciation '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
        ]
        return headers
    
    def _get_report_name(self):
        """
        报表名称
        """
        return _("Asset analysis report")
    
    def _get_templates(self):
        """
        模板调用
        :return: templates
        """
        templates = super(PsAssetAnalysisReport, self)._get_templates()
        templates['main_template'] = 'ps_account_asset.template_asset_analysis_report'
        try:
            self.env['ir.ui.view'].get_view_id('ps_account_asset.template_asset_analysis_line_report')
            templates['line_template'] = 'ps_account_asset.template_asset_analysis_line_report'
            templates['search_template'] = 'ps_account_asset.search_template_asset_analysis'
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
        lines=[]
        date_from = options.get('date').get('date_from')
        date_to = options.get('date').get('date_to')
        analytic_increase_style_para = options.get('analytic_increase_style').get('analytic_increase_style_para')
        asset_type_from = options.get('asset_type').get('asset_type_from')
        if options.get('analytic_increase_style').get('analytic_increase_style_para') == '0':
            is_all_increase_type = True
        else:
            is_all_increase_type = False
        if options.get('asset_type').get('asset_type_from') == '0':
            is_all_type = True
        else:
            is_all_type = False
        lines = []
        rows = []
        sql = """\
                SELECT pacm.category,aac.name,aaa.code,aaa.name,paal.former_quantity,paal.latter_quantity,
                    paal.former_value,paal.latter_value,paal.former_depreciation,paal.latter_depreciation
                FROM ps_asset_alteration_line paal
                LEFT JOIN ps_asset_alteration paa ON paa.id = paal.alteration_id
                LEFT JOIN account_asset_asset aaa ON aaa.id = paal.asset_id
                LEFT JOIN account_asset_category aac ON aac.id = aaa.category_id
                LEFT JOIN ps_asset_change_mode pacm ON pacm.id = paa.change_id
                WHERE paa.change_date >= cast(\'%s\' as date)
                AND paa.change_date <= cast(\'%s\' as date)
                AND CASE WHEN %s THEN 1=1
                ELSE pacm.category = \'%s\' END
                AND CASE WHEN %s THEN 1=1
                ELSE aac.id = %s END
        """%(date_from,date_to,is_all_increase_type,analytic_increase_style_para, is_all_type, asset_type_from)
        self.env.cr.execute(sql)
        analysis = self.env.cr.fetchall()
        for ana in analysis:
            categ = ana[0]
            if categ == 'add':
                categ = _(' Add')
            elif categ == 'reduce':
                categ = _(' Reduce')
            rows.append({
                'Increase Or Decrease': categ,
                'Asset Category': ana[1],
                'Asset Code': ana[2],
                'Asset': ana[3],
                'Former Quantity': ana[4],
                'Latter Quantity': ana[5],
                'Former Value': ana[6],
                'Latter Value': ana[7],
                'Former Accumulated Depreciation': ana[8],
                'Latter Accumulated Depreciation': ana[9],
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
        title_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'left': 2, 'right': 2, 'align': 'center',
             'valign': 'vcenter'})
        level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
        level_0_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'left'})
        level_0_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'right'})
        ctx = self._set_context(options)
        ctx.update({'no_format': True, 'print_mode': True})
        lines = self.with_context(ctx)._get_lines(options)
        for line in lines:
            print_id = line['id']
            for y in range(0, len(lines)):
                sheets = locals()
                sheets[y] = workbook.add_worksheet('sheet' + str(y))
                for index, column in enumerate(self._get_columns_name(options)):
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
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Increase Or Decrease'), style_left)
                        if x == 1:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Asset Category'), style_left)
                        if x == 2:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Asset Code') if lines[y]['columns'][
                                z - num].get('Asset Code') else '', style_left)
                        if x == 3:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Asset'), style_left)
                        if x == 4:
                            sheets[y].write(z, x,
                                            lines[y]['columns'][z - num].get('Former Quantity'),
                                            style_right)
                        if x == 5:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Latter Quantity'), style_right)
                        if x == 6:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Former Value'),
                                            style_right)
                        if x == 7:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Latter Value'), style_right)
                        if x == 8:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Former Accumulated Depreciation'), style_right)
                        if x == 9:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('Latter Accumulated Depreciation'), style_right)
        
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
