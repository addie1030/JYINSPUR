from odoo import models, fields, api, _
import copy
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo import tools
from odoo.addons import decimal_precision as dp


# 出库成本计算查询主类
class ReportStockSummary(models.AbstractModel):
    _name = "inventory.summary.report"
    _description = _("Inventory Summary Report")
    _inherit = 'account.report'

    filter_analytic = None
    # filter_date = {}
    filter_subject = {}
    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_year'}

    # 获取当前会计区间
    @api.model
    def get_currentperiod(self):
        currentdate = datetime.today().strftime("%Y-%m-%d")
        period_record_ids = self.env['ps.account.period'].get_period(currentdate)
        if period_record_ids == False:
            raise ValidationError(
                _('Did not find the corresponding accounting period, please maintain the period first!'))
        if len(period_record_ids) > 1:
            raise ValidationError(_('Find multiple accounting periods, please adjust the period first!'))
        # fyearperiod:该年度的值为当前会计年度，会计区间是当前区间
        fyear = period_record_ids[0].year
        fperiod = period_record_ids[0].period
        fyearperiod = fyear + fperiod
        return fyearperiod

    # 获取上一个跨级区间，如果存在非01-12的会计区间，应该考虑限定区间编号不允许修改
    @api.model
    def get_previousperiod(self, currperiod):
        if currperiod:
            cyear = currperiod[0:4]
            cperiod = currperiod[4:6]

            previousperiod = str(int(cperiod) - 1)
            if previousperiod == '0':
                previousperiod = '12'
                previousyear = str(int(cyear) - 1)
                previousline = period_line = self.env['ps.account.period'].search(
                    [('year', '=', previousyear), ('period', '=', previousperiod),
                     ('company_id', '=', self.env.user.company_id.id)])

                if previousline:
                    if previousline.year:
                        return previousyear + previousperiod
                    else:
                        return currperiod
                else:
                    return currperiod
            else:
                if int(previousperiod) < 10:
                    previousperiod = '0' + previousperiod

                previousline = period_line = self.env['ps.account.period'].search(
                    [('year', '=', cyear), ('period', '=', previousperiod),
                     ('company_id', '=', self.env.user.company_id.id)])
                if previousline:
                    if previousline.year:
                        return cyear + previousperiod
                    else:
                        return currperiod
                else:
                    return currperiod
        else:
            return currperiod

    # 查询标题
    def _get_report_name(self):
        return _("Inventory Summary Report")

    # 查询表头
    def _get_columns_name(self, options):
        headers = [[
            {'name': _(' Material Name '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 8%;background-color:#0073C6;color:white',
             'rowspan': '2'},
            {'name': _(' Material Internal Reference '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 8%;background-color:#0073C6;color:white',
             'rowspan': '2'},
            {'name': _(' Product Category '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 8%;background-color:#0073C6;color:white',
             'rowspan': '2'},
            {'name': _(' Company '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 8%;background-color:#0073C6;color:white',
             'rowspan': '2'},
            {'name': _(' Initial Balance '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
             'colspan': '3'},
            {'name': _(' Current Income '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
             'colspan': '3'},
            {'name': _(' Current Expenditure '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
             'colspan': '3'},
            {'name': _(' Final Balance '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap;width: 15%;background-color:#0073C6;color:white',
             'colspan': '3'}
        ],
            [
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Unit Price '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Unit Price '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Unit Price '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Unit Price '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'}
            ]]
        return headers

    # 查询模板
    def _get_templates(self):
        templates = super(ReportStockSummary, self)._get_templates()
        templates['main_template'] = 'ps_stock_account.template_inventory_summary_reports'
        try:
            self.env['ir.ui.view'].get_view_id('ps_stock_account.template_stock_summary_line_report')
            templates['line_template'] = 'ps_stock_account.template_stock_summary_line_report'
            templates['search_template'] = 'ps_stock_account.search_template_china'
        except ValueError:
            pass
        return templates

    # 显示按钮及对应事件
    def _get_reports_buttons(self):
        return [{'name': _('Print Preview'), 'action': 'print_pdf'},
                {'name': _('Export (XLSX)'), 'action': 'print_xlsx'}]

    # 计算并归集数据逻辑，更新库存物料余额表
    @api.model
    def _get_lines(self, options, line_id=None):
        precision = 2
        fyearperiod = self.get_currentperiod()
        period = self._context.get('period', fyearperiod)
        recalc = self._context.get('recalc', '0')

        fiscalyear = period[0:4]
        fiscalperiod = period[4:6]
        period_line = self.env['ps.account.period'].search([('year', '=', fiscalyear), ('period', '=', fiscalperiod),
                                                            ('company_id', '=', self.env.user.company_id.id)])

        if period_line:
            date_start = period_line.date_start
            date_end = period_line.date_end
        else:
            date_start = datetime.today().strftime("%Y-%m-%d")
            date_end = datetime.today().strftime("%Y-%m-%d")

        lines = []
        line_num = 1

        sql = """
            SELECT COUNT(*) FROM PS_STOCK_MATERIAL_BALANCE_TABLE
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
            rows = self._get_row(fiscalyear, fiscalperiod, self.env.user.company_id.id)
            lines.append({
                'id': line_num,
                'class': '',
                'level': 0,
                'columns': rows,
            })
        return lines

    # 获取库存物料余额表源数据并推送前端
    def _get_row(self, fiscalyear, fiscalperiod, company_id):
        result = []
        sample = {'name': '', 'default_code': '', 'categ_id': '', 'company_id': '', 'warehouse_id': '',
                  'begin_qty': 0, 'begin_price': 0, 'begin_value': 0,
                  'current_in_qty': 0, 'current_in_price': 0, 'current_in_value': 0,
                  'current_out_qty': 0, 'current_out_price': 0, 'current_out_value': 0,
                  'final_qty': 0, 'final_price': 0, 'final_value': 0}
        sql = """
                    SELECT 
                    PS_ACCOUNT_PERIOD.year as accounting_year, 
                    PS_ACCOUNT_PERIOD.period as accounting_period, 
                    PS_STOCK_MATERIAL_BALANCE_TABLE.company_id as company_id, 
                    product_id,
                    begin_qty, begin_price, begin_value,
                    current_in_qty, current_in_price, current_in_value,
                    current_out_qty, current_out_price, current_out_value,
                    final_qty, final_price, final_value
                    FROM PS_STOCK_MATERIAL_BALANCE_TABLE 
                    JOIN PS_ACCOUNT_PERIOD
                    ON PS_STOCK_MATERIAL_BALANCE_TABLE.accounting_period_id = PS_ACCOUNT_PERIOD.id
                    WHERE PS_ACCOUNT_PERIOD.YEAR =   '""" + fiscalyear + """' 
                    AND PS_ACCOUNT_PERIOD.PERIOD =  '""" + fiscalperiod + """' 
                    AND PS_STOCK_MATERIAL_BALANCE_TABLE.company_id = %s
                    ORDER BY accounting_year, accounting_period, company_id, product_id
            """ % (company_id)
        # print(sql)
        summary = copy.copy(sample)
        summary_begin_qty = 0
        summary_begin_price = 0
        summary_begin_value = 0
        summary_current_out_qty = 0
        summary_current_out_price = 0
        summary_current_out_value = 0
        summary_current_in_qty = 0
        summary_current_in_price = 0
        summary_current_in_value = 0
        summary_final_qty = 0
        summary_final_price = 0
        summary_final_value = 0

        self.env.cr.execute(sql)
        stock_material_balance_table_ids = self.env.cr.fetchall()
        for infos_line in stock_material_balance_table_ids:
            item = copy.copy(sample)
            productid = infos_line[3]
            if not productid:
                continue
            productline = self.env['product.template'].search([('id', '=', productid)])
            if not productline:
                continue
            productname = productline.name
            default_code = productline.default_code
            categ_id = productline.categ_id.name
            warehouse_id = productline.warehouse_id
            item['name'] = productname
            item['default_code'] = default_code
            item['categ_id'] = categ_id
            item['company_id'] = self.env.user.company_id.name
            item['warehouse_id'] = ''
            item['begin_qty'] = infos_line[4]
            item['begin_price'] = infos_line[5]
            item['begin_value'] = infos_line[6]
            item['current_in_qty'] = infos_line[7]
            item['current_in_price'] = infos_line[8]
            item['current_in_value'] = infos_line[9]
            item['current_out_qty'] = infos_line[10]
            item['current_out_price'] = infos_line[11]
            item['current_out_value'] = infos_line[12]
            item['final_qty'] = infos_line[13]
            item['final_price'] = infos_line[14]
            item['final_value'] = infos_line[15]
            result.append(item)
            summary_begin_qty += infos_line[4]
            summary_begin_value += infos_line[6]
            summary_current_in_qty += infos_line[7]
            summary_current_in_value += infos_line[9]
            summary_current_out_qty += infos_line[10]
            summary_current_out_value += infos_line[12]
            summary_final_qty += infos_line[13]
            summary_final_value += infos_line[15]

        precision_q = dp.get_precision('Product Unit of Measure')(self.env.cr)
        precision_v = dp.get_precision('Account')(self.env.cr)
        summary['name'] = _('Total')
        summary['default_code'] = ''
        summary['categ_id'] = ''
        summary['company_id'] = ''
        summary['warehouse_id'] = ''
        summary['begin_qty'] = round(summary_begin_qty, precision_q[1])
        summary['begin_price'] = 0
        summary['begin_value'] = round(summary_begin_value, precision_v[1])
        summary['current_in_qty'] = round(summary_current_in_qty, precision_q[1])
        summary['current_in_price'] = 0
        summary['current_in_value'] = round(summary_current_in_value, precision_v[1])
        summary['current_out_qty'] = round(summary_current_out_qty, precision_q[1])
        summary['current_out_price'] = 0
        summary['current_out_value'] = round(summary_current_out_value, precision_v[1])
        summary['final_qty'] = round(summary_final_qty, precision_q[1])
        summary['final_price'] = 0
        summary['final_value'] = round(summary_final_value, precision_v[1])
        result.append(summary)
        return result

    # 设置搜索条件
    @api.model
    def get_options(self, previous_options=None):
        # Be sure that user has group analytic if a report tries to display analytic
        return self._build_options(previous_options)

    def apply_date_filter(self, options):
        return options

    def apply_cmp_filter(self, options):
        return options

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

