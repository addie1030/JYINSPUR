from odoo import models, fields, api, _
import copy
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo import tools
from odoo.addons import decimal_precision as dp
import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    # TODO saas-17: remove the try/except to directly import from misc
    import xlsxwriter


# 库存物料余额表数据结构定义
class PsStockMaterialBalanceTable(models.Model):
    _name = 'ps.stock.material.balance.table'
    _description = _('Stock Material Balance Table')

    accounting_period_id = fields.Many2one('ps.account.period', string=_('Fiscal Period'),
                                           default=lambda self: self.env['ps.account.period'].get_current_period()[2])
    company_id = fields.Many2one('res.company', string=_('Company'), required=True,
                                 default=lambda self: self.env.user.company_id)
    product_id = fields.Many2one('product.product', string=_('Product'), required=True)
    begin_qty = fields.Float(string=_('Initial Quantity'), digits=dp.get_precision('Product Unit of Measure'))
    begin_price = fields.Float(string=_('Initial Price'), digits=dp.get_precision('Product Price'))
    begin_value = fields.Float(string=_('Initial Amount'), digits=dp.get_precision('Account'))
    current_out_qty = fields.Float(string=_('Current Issue Quantity'),
                                   digits=dp.get_precision('Product Unit of Measure'))
    current_out_price = fields.Float(string=_('Current Issue Price'), digits=dp.get_precision('Product Price'))
    current_out_value = fields.Float(string=_('Current Issue Amount'), digits=dp.get_precision('Account'))
    current_in_qty = fields.Float(string=_('Current Income Quantity'),
                                  digits=dp.get_precision('Product Unit of Measure'))
    current_in_price = fields.Float(string=_('Current Income Price'), digits=dp.get_precision('Product Price'))
    current_in_value = fields.Float(string=_('Current Income Amount'), digits=dp.get_precision('Account'))
    final_qty = fields.Float(string=_('Final Balance Quantity'), digits=dp.get_precision('Product Unit of Measure'))
    final_price = fields.Float(string=_('Final Balance Price'), digits=dp.get_precision('Product Price'))
    final_value = fields.Float(string=_('Final Balance Amount'), digits=dp.get_precision('Account'))


# 出库成本计算查询主类
class ReportStockOutboundCostCalculation(models.AbstractModel):
    _name = "outbound.cost.calculation.report"
    _description = "Outbound Cost Calculation"
    _inherit = 'account.report'

    filter_analytic = None
    filter_subject = {}
    # filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_year'}

    # 获取当前会计区间
    @api.model
    def get_currentperiod(self):
        currentdate = datetime.today().strftime("%Y-%m-%d")
        period_record_ids = self.env['ps.account.period'].get_period(currentdate)
        if period_record_ids == False:
            raise ValidationError('Did not find the corresponding accounting period, please maintain the period first!')
        if len(period_record_ids) > 1:
            raise ValidationError('Find multiple accounting periods, please adjust the period first!')
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
        return _("Outbound Cost Calculation")

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
            {'name': _(' Warehouse '), 'class': 'string',
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
        templates = super(ReportStockOutboundCostCalculation, self)._get_templates()
        templates['main_template'] = 'ps_stock_account.template_outbound_cost_calculation_reports'
        try:
            self.env['ir.ui.view'].get_view_id(
                'ps_stock_account.template_outbound_cost_calculation_line_report')
            templates['line_template'] = 'ps_stock_account.template_outbound_cost_calculation_line_report'
            templates['search_template'] = 'ps_stock_account.search_template_china'
        except ValueError:
            pass
        return templates

    # 导出xlsx
    def get_xlsx(self, options, response):
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
        ctx = self.set_context(options)
        ctx.update({'no_format': True, 'print_mode': True})
        lines = self.with_context(ctx).get_lines(options)

        if options.get('hierarchy'):
            lines = self.create_hierarchy(lines)

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
            res = self.get_columns_name(options)
            for column in self.get_columns_name(options):
                if len(res) == 2:
                    if len(column) == 9:
                        for item in column:
                            if 'rowspan' in item:
                                sheets[y].merge_range(1, x, 2, x,
                                                      item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),
                                                      title_style)
                                x += 1
                            elif 'colspan' in item:
                                sheets[y].merge_range(1, x, 1, x + 2,
                                                      item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),
                                                      title_style)
                                x = x + 3
                    else:
                        w = 5
                        for item in column:
                            sheets[y].write(2, w, item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),
                                            title_style)
                            w += 1
                    num = 3
                    wid = 17
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
                    if wid <= 7:
                        if x == 0:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('date'), style_left)
                        if x == 1:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('name'), style)
                        if x == 2:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('summary'), style)
                        if x == 3:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('debit'), style_right)
                        if x == 4:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('credit'), style_right)
                        if x == 5:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('direction'), style)
                        if x == 6:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('f_balance'), style_right)
                    elif wid == 17:
                        if x == 0:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('name'), style)
                        if x == 1:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('default_code'), style)
                        if x == 2:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('categ_id'), style)
                        if x == 3:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('company_id'), style)
                        if x == 4:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('warehouse_id'), style)
                        if x == 5:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('begin_qty'), style_right)
                        if x == 6:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('begin_price'), style_right)
                        if x == 7:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('begin_value'), style_right)
                        if x == 8:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('current_in_qty'), style_right)
                        if x == 9:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('current_in_price'), style_right)
                        if x == 10:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('current_in_value'), style_right)
                        if x == 11:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('current_out_qty'), style_right)
                        if x == 12:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('current_out_price'), style_right)
                        if x == 13:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('current_out_value'), style_right)
                        if x == 14:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('final_qty'), style_right)
                        if x == 15:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('final_price'), style_right)
                        if x == 16:
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('final_value'), style_right)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    # 计算并归集数据逻辑，更新库存物料余额表
    @api.model
    def _get_lines(self, options, line_id=None):
        precision_p = dp.get_precision('Product Price')(self.env.cr)
        precision_q = dp.get_precision('Product Unit of Measure')(self.env.cr)
        precision_v = dp.get_precision('Account')(self.env.cr)
        fyearperiod = self.get_currentperiod()
        period = self._context.get('period', fyearperiod)
        # recalc:'0'显示已有数据，'1'计算，默认显示已有数据
        recalc = self._context.get('recalc', '0')

        fiscalyear = period[0:4]
        fiscalperiod = period[4:6]
        period_line = self.env['ps.account.period'].search([('year', '=', fiscalyear), ('period', '=', fiscalperiod),
                                                            ('company_id', '=', self.env.user.company_id.id)])

        if period_line:
            date_start = str(period_line.date_start)
            date_end = str(period_line.date_end) + ' 23:59:59'
        else:
            date_start = datetime.today().strftime("%Y-%m-%d")
            date_end = datetime.today().strftime("%Y-%m-%d") + ' 23:59:59'

        lines = []
        line_num = 1
        # 验证存在入库单据成本价格为0的单据
        sql = """
            SELECT STOCK_MOVE.PRICE_UNIT as price FROM STOCK_MOVE LEFT JOIN STOCK_PICKING ON STOCK_MOVE.PICKING_ID = STOCK_PICKING.ID
            LEFT JOIN STOCK_PICKING_TYPE ON STOCK_PICKING.PICKING_TYPE_ID = STOCK_PICKING_TYPE.ID
            WHERE STOCK_PICKING_TYPE.CODE = 'incoming' 
            AND STOCK_MOVE.STATE = 'done' 
            AND STOCK_PICKING.COMPANY_ID = '""" + str(self.env.user.company_id.id) + """' 
            AND (STOCK_PICKING.DATE >= '""" + date_start + """' 
            AND STOCK_PICKING.DATE <= '""" + date_end + """')
        """
        self.env.cr.execute(sql)
        price_ids = self.env.cr.fetchall()

        if price_ids:
            ispricezero = False
            for line in price_ids:
                if line:
                    if line[0] == None:
                        ispricezero = True
                        break
                    if line[0] == 0:
                        ispricezero = True
                        break
            if ispricezero:
                raise ValidationError('存在入库单据成本价格为0的单据，需要先通过入库成本维护功能进行成本维护。')
                return

        # 验证存在已生成凭证的单据//修改为已生成凭证的出库单，不验证入库单
        sql = """
            SELECT STOCK_PICKING.ID AS stockid 
            FROM STOCK_PICKING LEFT JOIN STOCK_MOVE ON STOCK_PICKING.ID = STOCK_MOVE.PICKING_ID 
            LEFT JOIN STOCK_PICKING_TYPE ON STOCK_PICKING.PICKING_TYPE_ID = STOCK_PICKING_TYPE.ID
            WHERE STOCK_MOVE.account_move_id IS NOT NULL 
            AND STOCK_PICKING_TYPE.CODE = 'outgoing' 
            AND STOCK_MOVE.account_move_id > 0
            AND STOCK_MOVE.STATE = 'done' 
            AND STOCK_PICKING.COMPANY_ID = '""" + str(self.env.user.company_id.id) + """' 
            AND (STOCK_PICKING.DATE >= '""" + date_start + """' 
            AND STOCK_PICKING.DATE <= '""" + date_end + """')
            """
        self.env.cr.execute(sql)
        moved_ids = self.env.cr.fetchall()

        if moved_ids:
            ismoved = False
            for line in moved_ids:
                if line:
                    ismoved = True
                    break
                else:
                    if line.stockid is None:
                        ismoved = True
                        break
            if ismoved:
                raise ValidationError('存在已生成凭证的单据，需要先取消凭证重新进行计算。')
                return

        if recalc == '1':
            ####计算过程
            ##计算期初：
            # 由于“初始核算数据维护”未实现，
            # 所以当前的逻辑是如果计算期间是启用期间的话，数量和金额就是0
            # 非启用期间的话就是上期的结存数量和金额
            # 获取上个会计区间，如果上个会计区间的值等于当前会计区间的值，说明没有找到上个会计区间，
            # 没有上一个区间说明是启用期间
            # [{'product1':[1,2,3]},{'product2':[2,3,4]}]
            # [{'name':'product1','qty':1,'value':2,'price':3},{'name':'product2','qty':2,'value':3,'price':4}]

            previousperiod = self.get_previousperiod(period)
            preyear = previousperiod[0:4]
            preperiod = previousperiod[4:6]

            final_products_infos = []
            product_infos = {}
            pre_price_ids = []

            sql = """
                SELECT 
                MAX(PRODUCT_ID) AS productid,
                MAX(FINAL_QTY) AS totalqty,
                MAX(FINAL_VALUE) AS totalamount 
                FROM PS_STOCK_MATERIAL_BALANCE_TABLE 
                JOIN PS_ACCOUNT_PERIOD
                ON PS_STOCK_MATERIAL_BALANCE_TABLE.accounting_period_id = PS_ACCOUNT_PERIOD.id
                WHERE PS_ACCOUNT_PERIOD.YEAR =   '""" + preyear + """' 
                AND PS_ACCOUNT_PERIOD.PERIOD =  '""" + preperiod + """' 
                AND PS_STOCK_MATERIAL_BALANCE_TABLE.COMPANY_ID = '""" + str(self.env.user.company_id.id) + """' 
                GROUP BY PRODUCT_ID
                """
            self.env.cr.execute(sql)
            pre_price_ids = self.env.cr.fetchall()

            if pre_price_ids:
                for pre_line in pre_price_ids:
                    productid = pre_line[0]
                    if previousperiod == period:
                        beginqty = 0
                        beginvalue = 0
                        beginprice = 0
                    else:
                        beginqty = pre_line[1]
                        beginvalue = pre_line[2]
                        beginprice = round(beginvalue / beginqty, precision_p[1])
                    product_infos['productid'] = productid
                    product_infos['begin_qty'] = beginqty
                    product_infos['begin_value'] = beginvalue
                    product_infos['begin_price'] = beginprice

                    product_infos['current_out_qty'] = 0
                    product_infos['current_out_value'] = 0
                    product_infos['current_out_price'] = 0

                    product_infos['current_in_qty'] = 0
                    product_infos['current_in_value'] = 0
                    product_infos['current_in_price'] = 0

                    product_infos['final_qty'] = 0
                    product_infos['final_value'] = 0
                    product_infos['final_price'] = 0
                    final_products_infos.append(product_infos)

            stock_incoming_ids = self.env['stock.move'].search([('state', '=', 'done'),('company_id', '=', self.env.user.company_id.id),('date', '>=', date_start),('date', '<=', date_end)])
            # 初始没有，收入没有，不记录
            # 初始有，收入没有，不处理
            # 初始没有，收入有，新增记录
            # 初始有，收入有，更新
            if not stock_incoming_ids:
                raise ValidationError('未检测到符合条件的入库单据，请检查。')

            #只循环入库记录，确定产品入库的价格
            for stock_incoming_line in stock_incoming_ids:
                existproductid = False
                if stock_incoming_line.picking_id.picking_type_id.code != 'incoming':
                    continue

                for i in range(len(final_products_infos)):
                    product_infos = final_products_infos[i]
                    if product_infos['productid'] == stock_incoming_line.product_id.id:
                        existproductid = True
                        final_products_infos[i]['current_in_qty'] += stock_incoming_line.product_qty
                        if stock_incoming_line.product_id.cost_method == 'onemonth':
                            final_products_infos[i]['current_in_value'] += round(stock_incoming_line.price_unit * stock_incoming_line.product_qty, precision_v[1])
                            final_products_infos[i]['current_in_price'] = round(final_products_infos[i]['current_in_value'] / final_products_infos[i]['current_in_qty'], precision_p[1])
                        elif stock_incoming_line.product_id.cost_method == 'standard':
                            final_products_infos[i]['current_in_price'] = stock_incoming_line.product_id.standard_price
                            final_products_infos[i]['current_in_value'] += round(stock_incoming_line.product_id.standard_price * stock_incoming_line.product_qty, precision_v[1])
                        elif stock_incoming_line.product_id.cost_method in ['average', 'fifo']:
                            final_products_infos[i]['current_in_value'] += stock_incoming_line.value
                            final_products_infos[i]['current_in_price'] = round(final_products_infos[i]['current_in_value'] / final_products_infos[i]['current_in_qty'], precision_p[1])
                        else:
                            pass
                        break

                if not existproductid:
                    product_infos = {}
                    product_infos['productid'] = stock_incoming_line.product_id.id
                    product_infos['begin_qty'] = 0
                    product_infos['begin_value'] = 0
                    product_infos['begin_price'] = 0

                    product_infos['current_out_qty'] = 0
                    product_infos['current_out_value'] = 0
                    product_infos['current_out_price'] = 0

                    product_infos['current_in_qty'] = stock_incoming_line.product_qty
                    if stock_incoming_line.product_id.cost_method == 'onemonth':
                        product_infos['current_in_value'] = round(
                            stock_incoming_line.price_unit * stock_incoming_line.product_qty, precision_v[1])
                        product_infos['current_in_price'] = stock_incoming_line.price_unit
                    elif stock_incoming_line.product_id.cost_method == 'standard':
                        product_infos['current_in_price'] = stock_incoming_line.product_id.standard_price
                        product_infos['current_in_value'] = round(
                            stock_incoming_line.product_id.standard_price * stock_incoming_line.product_qty, precision_v[1])
                    elif stock_incoming_line.product_id.cost_method in ['average', 'fifo']:
                        product_infos['current_in_value'] = stock_incoming_line.value
                        product_infos['current_in_price'] = round(
                            stock_incoming_line.value / stock_incoming_line.product_qty, precision_p[1])
                    else:
                        pass

                    product_infos['final_qty'] = 0
                    product_infos['final_value'] = 0
                    product_infos['final_price'] = 0
                    final_products_infos.append(product_infos)


            ## 入库单成本价格更新出库单成本价格
            # 需要更新成本的出库单据
            stock_outgoing_ids = self.env['stock.move'].search(
                [('state', '=', 'done'), ('company_id', '=', self.env.user.company_id.id), ('date', '>=', date_start),
                 ('date', '<=', date_end)])

            # 初始+收入没有，发出没有，不记录
            # 初始+收入有，发出没有，不处理
            # 初始+收入没有，发出有，新增记录
            # 初始+收入有，发出有，更新
            if stock_outgoing_ids:
                product_qty = 0
                value = 0
                for stock_outgoing_line in stock_outgoing_ids:
                    if stock_outgoing_line.picking_id.picking_type_id.code != 'outgoing':
                        continue

                    product_infos = {}
                    existproductid = False
                    for i in range(len(final_products_infos)):
                        product_infos = final_products_infos[i]
                        if product_infos['productid'] == stock_outgoing_line.product_id.id:
                            existproductid = True
                            if stock_outgoing_line.product_id.cost_method == 'onemonth':
                                # 更新出库单据的单价和金额--全月一次加权平均
                                stock_value = product_infos['current_in_price'] * stock_outgoing_line.product_qty
                                stock_outgoing_line.write({'value': -stock_value, 'price_unit': -product_infos['current_in_price']})
                                # 归集该产品的出库数量和金额，因为odoo中的出库单价和金额记为负数，根据习惯，取正数显示
                                final_products_infos[i]['current_out_qty'] += stock_outgoing_line.product_qty
                                final_products_infos[i]['current_out_value'] += stock_value
                                final_products_infos[i]['current_out_price'] = product_infos['current_in_price']
                            if stock_outgoing_line.product_id.cost_method in ['standard', 'average', 'fifo']:
                                # 归集该产品的出库数量和金额，因为odoo中的出库单价和金额记为负数，根据习惯，取正数显示
                                final_products_infos[i]['current_out_qty'] += stock_outgoing_line.product_qty
                                final_products_infos[i]['current_out_value'] += - stock_outgoing_line.value
                                final_products_infos[i]['current_out_price'] = round(final_products_infos[i]['current_out_value'] / final_products_infos[i]['current_out_qty'], precision_v[1])

                            break
                    if not existproductid:
                        product_infos = {}
                        product_infos['productid'] = stock_outgoing_line.product_id.id
                        product_infos['begin_qty'] = 0
                        product_infos['begin_value'] = 0
                        product_infos['begin_price'] = 0

                        product_infos['current_in_qty'] = 0
                        product_infos['current_in_value'] = 0
                        product_infos['current_in_price'] = 0

                        product_infos['current_out_qty'] = stock_outgoing_line.product_qty
                        product_infos['current_out_value'] = - stock_outgoing_line.value
                        product_infos['current_out_price'] = - stock_outgoing_line.price_unit

                        product_infos['final_qty'] = 0
                        product_infos['final_value'] = 0
                        product_infos['final_price'] = 0
                        final_products_infos.append(product_infos)

            #创建或者更新库存物料余额表
            if final_products_infos:
                for i in range(len(final_products_infos)):
                    product_infos = final_products_infos[i]
                    final_qty = product_infos['begin_qty'] + product_infos['current_in_qty'] - product_infos[
                        'current_out_qty']
                    final_value = round(product_infos['begin_value'] + product_infos['current_in_value'] - product_infos[
                        'current_out_value'], precision_v[1])
                    line_ids = self.env['ps.stock.material.balance.table'].search(
                        [('product_id', '=', product_infos['productid']),
                         ('accounting_period_id.year', '=', fiscalyear),
                         ('accounting_period_id.period', '=', fiscalperiod)])
                    final_price = 0
                    if final_qty != 0:
                        final_price = round(final_value / final_qty, precision_p[1])
                    if line_ids:
                        line_ids.write({'begin_qty': product_infos['begin_qty'],
                                        'begin_price': product_infos['begin_price'],
                                        'begin_value': product_infos['begin_value'],
                                        'current_out_qty': product_infos['current_out_qty'],
                                        'current_out_price': product_infos['current_out_price'],
                                        'current_out_value': product_infos['current_out_value'],
                                        'current_in_qty': product_infos['current_in_qty'],
                                        'current_in_price': product_infos['current_in_price'],
                                        'current_in_value': product_infos['current_in_value'],
                                        'final_qty': final_qty,
                                        'final_price': final_price,
                                        'final_value': final_value
                                        })
                    else:
                        maxid = self.env['ps.stock.material.balance.table'].create({
                            # 'accounting_period_id.year': fiscalyear,
                            # 'accounting_period_id.period': fiscalperiod,
                            'company_id': self.env.user.company_id.id,
                            'product_id': product_infos['productid'],
                            'begin_qty': product_infos['begin_qty'],
                            'begin_price': product_infos['begin_price'],
                            'begin_value': product_infos['begin_value'],
                            'current_out_qty': product_infos['current_out_qty'],
                            'current_out_price': product_infos['current_out_price'],
                            'current_out_value': product_infos['current_out_value'],
                            'current_in_qty': product_infos['current_in_qty'],
                            'current_in_price': product_infos['current_in_price'],
                            'current_in_value': product_infos['current_in_value'],
                            'final_qty': final_qty,
                            'final_price': final_price,
                            'final_value': final_value,
                        })
                        if not maxid:
                            raise ValidationError(_('Error inserting report line information, please check!'))
                            break

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
        precision_p = dp.get_precision('Product Price')(self.env.cr)
        precision_q = dp.get_precision('Product Unit of Measure')(self.env.cr)
        precision_v = dp.get_precision('Account')(self.env.cr)
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

        summary['name'] = _('Total')
        summary['default_code'] = ''
        summary['categ_id'] = ''
        summary['company_id'] = ''
        summary['warehouse_id'] = ''
        summary['begin_qty'] = summary_begin_qty
        summary['begin_price'] = 0
        summary['begin_value'] = round(summary_begin_value, precision_v[1])
        summary['current_in_qty'] = summary_current_in_qty
        summary['current_in_price'] = 0
        summary['current_in_value'] = round(summary_current_in_value, precision_v[1])
        summary['current_out_qty'] = summary_current_out_qty
        summary['current_out_price'] = 0
        summary['current_out_value'] = round(summary_current_out_value, precision_v[1])
        summary['final_qty'] = summary_final_qty
        summary['final_price'] = 0
        summary['final_value'] = round(summary_final_value, precision_v[1])
        result.append(summary)
        return result

    # 设置搜索条件
    @api.model
    def get_options(self, previous_options=None):
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
