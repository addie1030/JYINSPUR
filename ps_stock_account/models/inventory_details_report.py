import io
from odoo.addons import decimal_precision as dp

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    # TODO saas-17: remove the try/except to directly import from misc
    import xlsxwriter
from odoo import models, fields, api, _
import copy
from odoo.exceptions import ValidationError


class InventoryDetailsReport(models.AbstractModel):
    _name = "inventory.details.report"
    _description = _("Inventory Details Report")
    _inherit = 'account.report'

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
                    if len(column) == 5:
                        for item in column:
                            if 'rowspan' in item:
                                sheets[y].merge_range(1, x, 2, x,
                                                      item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),
                                                      title_style)
                                x += 1
                            elif 'colspan' in item:
                                sheets[y].merge_range(1, x, 1, x + 1,
                                                      item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),
                                                      title_style)
                                x = x + 2
                    else:
                        w = 2
                        for item in column:
                            sheets[y].write(2, w, item.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '),
                                            title_style)
                            w += 1
                    num = 3
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
                            sheets[y].write(z, x, lines[y]['columns'][z - num].get('ending_balance_credit'),
                                            style_right)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_year'}
    filter_partner = {'partner_from': '1'}

    def _get_columns_name(self, options):
        headers = [[
            {'name': _(' Accounting Period '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white',
             'rowspan': '2'},
            {'name': _(' Company '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white',
             'rowspan': '2'},
            {'name': _(' Product Name '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white',
             'rowspan': '2'},
            {'name': _(' Product Category '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white',
             'rowspan': '2'},
            {'name': _(' Document Number '), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 10%;background-color:#0073C6;color:white',
             'rowspan': '2'},
            {'name': _('Income'), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 15%;background-color:#0073C6;color:white',
             'colspan': '3'},
            {'name': _('Expenditure'), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 15%;background-color:#0073C6;color:white',
             'colspan': '3'},
            {'name': _('Balance'), 'class': 'string',
             'style': 'text-align:center; white-space:nowrap; width: 15%;background-color:#0073C6;color:white',
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
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Unit Price '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Quantity '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white '},
                {'name': _(' Unit Price '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'},
                {'name': _(' Amount '), 'class': 'string',
                 'style': 'text-align:center; white-space:nowrap;width: 5%;background-color:#0073C6;color:white'}
            ]]
        return headers

    def _get_report_name(self):
        return _("Inventory Details Report")

    def _get_templates(self):
        templates = super(InventoryDetailsReport, self)._get_templates()
        templates['main_template'] = 'ps_stock_account.template_inventory_reports'
        try:
            self.env['ir.ui.view'].get_view_id('ps_account_center.template_account_china_fzyeb_line_report')
            templates['line_template'] = 'ps_account.template_account_china_fzyeb_line_report'
        except ValueError:
            pass
        return templates

    @api.model
    def _get_lines(self, options, line_id=None):
        date_from = options.get('date').get('date_from')
        date_to = options.get('date').get('date_to')
        partner_from = options.get('partner').get('partner_from')

        lines = []
        line_num = 1
        sql = """select
            t2.year||'.'||t2.period as 会计区间 , t6.name as 公司,
            t1.name as 产品名称,t4.name as 产品类别,t1.reference as 单据编号,
            case when t5.code='incoming' then t1.product_uom_qty else null end as 入数量,
            case when t5.code='incoming' then t1.price_unit else null end as 入单价,
            case when t5.code='incoming' then t1.value else null end as 入金额,
            case when t5.code='outgoing' then t1.product_uom_qty else null end as 出数量,
            case when t5.code='outgoing' then t1.price_unit else null end as 出单价,
            case when t5.code='outgoing' then t1.value else null end as 出金额,
            t5.code
            from stock_move t1,ps_account_period t2,product_template t3,product_category t4,stock_picking_type t5,res_company t6
            where
            (to_date(to_char(t1.date, 'yyyy-mm-dd'),'yyyy-mm-dd') >= t2.date_start 
             and 
             to_date(to_char(t1.date, 'yyyy-mm-dd'),'yyyy-mm-dd') <= t2.date_end)
            and t1.product_id = t3.id and t3.categ_id = t4.id and t1.picking_type_id = t5.id and t1.company_id = t6.id and t1.state = 'done'
            order by 会计区间,产品名称,t1.date """
        self.env.cr.execute(sql)
        temps = self.env.cr.fetchall()
        time = '0000.00'
        product = ''
        last_number = 0
        last_price = 0
        last_value = 0

        sql = """
                       SELECT COUNT(*) FROM ACCOUNT_MOVE
                    """
        self.env.cr.execute(sql)
        recordCount = self.env.cr.fetchone()[0]
        rows = []

        if len(temps) <= 0:
            return lines
        else:
            for temp in temps:
                # for subject in subjects:
                row = {}
                row['section'] = temp[0]
                row['company'] = temp[1]
                row['product'] = temp[2]
                row['product_category'] = temp[3]
                row['document_number'] = temp[4]
                row['in_number'] = temp[5]
                row['in_price'] = temp[6]
                row['in_value'] = temp[7]
                row['out_number'] = temp[8]
                row['out_price'] = temp[9]
                row['out_value'] = temp[10]

                if (row['section'] != time) or (row['product'] != product):
                    if temp[11] == 'incoming':
                        row['jc_number'] = temp[5]
                        row['jc_price'] = temp[6]
                        row['jc_value'] = temp[7]
                    else:
                        row['jc_number'] = temp[8]
                        row['jc_price'] = temp[9] if temp[9] == None else -temp[9]
                        row['jc_value'] = temp[10] if temp[10] == None else -temp[10]
                    time = row['section']
                    product = row['product']
                    last_number = row['jc_number']
                    last_value = row['jc_value']
                else:
                    precision_q = dp.get_precision('Product Unit of Measure')(self.env.cr)
                    precision_v = dp.get_precision('Account')(self.env.cr)
                    if temp[11] == 'incoming':
                        row['jc_number'] = round(last_number + row['in_number'], precision_q[1])
                        row['jc_value'] = round(last_value + (row['in_number'] * row['in_price']), precision_v[1])
                        row['jc_price'] = row['in_price']
                        last_number = row['jc_number']
                        last_value = row['jc_value']
                    else:
                        row['jc_number'] = None if row['out_number'] == None else round(last_number - row['out_number'],precision_q[1])
                        row['jc_value'] = None if row['out_number'] == None else round(last_value + (row['out_number'] * row['out_price']), precision_v[1])
                        row['jc_price'] = None if row['out_price'] == None else -row['out_price']
                        row['out_price'] = None if row['out_price'] == None else - row['out_price']
                        row['out_value'] = None if row['out_value'] == None else - row['out_value']
                        last_number = row['jc_number']
                        last_value = row['jc_value']

                lines.append({
                    'id': line_num,
                    'name': _("Exchange Unit: ") + temp[1],
                    'class': '',
                    'level': 0,
                    'columns': row,
                })
                # line_num += 1
        return lines
