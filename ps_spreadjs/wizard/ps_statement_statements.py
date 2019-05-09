from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class StatementOutput(models.TransientModel):
    _name = 'ps.statement.statements.output'
    _description = '转出数据'

    date = fields.Date(String='转出日期', default=fields.Date.context_today, required=True)
    report_code = fields.Char(String='报表编号')
    report_date = fields.Char(String='报表日期')
    report_name = fields.Char(String='报表名称')
    note = fields.Char(String='备注')

    @api.multi
    def statement_output(self):
        ac_move_ids = self._context.get('active_ids', False)
        print(ac_move_ids)
        return
        # res = self.env['account.move'].browse(ac_move_ids).reverse_moves(self.date, self.journal_id or False)
        # if res:
        #     return {
        #         'name': _('转出数据'),
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'tree,form',
        #         'res_model': 'ps.statement.statements',
        #         'domain': [('id', 'in', res)],
        #     }
        # return {'type': 'ir.actions.act_window_close'}

class StatementInput(models.TransientModel):
    _name = 'ps.statement.statements.input'
    _description = '转入数据'

    date = fields.Date(String='转入日期', default=fields.Date.context_today, required=True)
    report_code = fields.Char(String='报表编号')
    report_date = fields.Char(String='报表日期')
    report_name = fields.Char(String='报表名称')
    note = fields.Char(String='备注')

    @api.multi
    def statement_input(self):
        ac_move_ids = self._context.get('active_ids', False)
        print(ac_move_ids)
        return
        # res = self.env['account.move'].browse(ac_move_ids).reverse_moves(self.date, self.journal_id or False)
        # if res:
        #     return {
        #         'name': _('转入数据'),
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'tree,form',
        #         'res_model': 'ps.statement.statements',
        #         'domain': [('id', 'in', res)],
        #     }
        # return {'type': 'ir.actions.act_window_close'}

class StatementExport(models.TransientModel):
    _name = 'ps.statement.statements.export'
    _description = '导出报表'

    date = fields.Date(String='导出日期', default=fields.Date.context_today, required=True)
    report_code = fields.Char(String='报表编号')
    report_date = fields.Char(String='报表日期')
    report_name = fields.Char(String='报表名称')
    note = fields.Char(String='备注')

    @api.multi
    def statement_export(self):
        ac_move_ids = self._context.get('active_ids', False)
        print(ac_move_ids)
        return
        # res = self.env['account.move'].browse(ac_move_ids).reverse_moves(self.date, self.journal_id or False)
        # if res:
        #     return {
        #         'name': _('转出数据'),
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'tree,form',
        #         'res_model': 'ps.statement.statements',
        #         'domain': [('id', 'in', res)],
        #     }
        # return {'type': 'ir.actions.act_window_close'}

class StatementImport(models.TransientModel):
    _name = 'ps.statement.statements.import'
    _description = '导入报表'

    date = fields.Date(String='导入日期', default=fields.Date.context_today, required=True)
    report_code = fields.Char(String='报表编号')
    report_date = fields.Char(String='报表日期')
    report_name = fields.Char(String='报表名称')
    note = fields.Char(String='备注')

    @api.multi
    def statement_import(self):
        ac_move_ids = self._context.get('active_ids', False)
        print(ac_move_ids)
        return
        # res = self.env['account.move'].browse(ac_move_ids).reverse_moves(self.date, self.journal_id or False)
        # if res:
        #     return {
        #         'name': _('转入数据'),
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'tree,form',
        #         'res_model': 'ps.statement.statements',
        #         'domain': [('id', 'in', res)],
        #     }
        # return {'type': 'ir.actions.act_window_close'}

class StatementCalculate(models.TransientModel):
    _name = 'ps.statement.statements.calculate'
    _description = '计算报表'

    date = fields.Date(String='计算日期', default=fields.Date.context_today, required=True)
    report_code = fields.Char(String='报表编号')
    report_date = fields.Char(String='报表日期')
    report_name = fields.Char(String='报表名称')
    note = fields.Char(String='备注')

    @api.multi
    def statement_calculate(self):
        ac_move_ids = self._context.get('active_ids', False)
        print(ac_move_ids)
        return
        # res = self.env['account.move'].browse(ac_move_ids).reverse_moves(self.date, self.journal_id or False)
        # if res:
        #     return {
        #         'name': _('转入数据'),
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'tree,form',
        #         'res_model': 'ps.statement.statements',
        #         'domain': [('id', 'in', res)],
        #     }
        # return {'type': 'ir.actions.act_window_close'}

class StatementMonthEnd(models.TransientModel):
    _name = 'ps.statement.statements.monthend'
    _description = '月末存档'

    date = fields.Date(String='存档日期', default=fields.Date.context_today, required=True)
    report_code = fields.Char(String='报表编号')
    report_date = fields.Char(String='报表日期')
    report_name = fields.Char(String='报表名称')
    note = fields.Char(String='备注')

    # @api.multi
    # def statement_monthend(self):
    #     ac_move_ids = self._context.get('active_ids', False)
    #     print(ac_move_ids)
    #     return
    #     res = self.env['ps.statement.statements'].monthend(ac_move_ids)
    #     if res:
    #         return {
    #             'name': _('转入数据'),
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             'res_model': 'ps.statement.statements',
    #             'domain': [('id', 'in', res)],
    #         }
    #     return {'type': 'ir.actions.act_window_close'}


class StatementArchive(models.TransientModel):
    _name = 'ps.statement.statements.archive'
    _description = '报表封存'

    date = fields.Date(String='封存日期', default=fields.Date.context_today, required=True)
    report_code = fields.Char(String='报表编号')
    report_date = fields.Char(String='报表日期')
    report_name = fields.Char(String='报表名称')
    note = fields.Char(String='备注')

class StatementUnarchive(models.TransientModel):
    _name = 'ps.statement.statements.unarchive'
    _description = '报表启封'

    date = fields.Date(String='启封日期', default=fields.Date.context_today, required=True)
    report_code = fields.Char(String='报表编号')
    report_date = fields.Char(String='报表日期')
    report_name = fields.Char(String='报表名称')
    note = fields.Char(String='备注')

class NewStatement(models.TransientModel):
    _name = 'ps.statement.statements.newstatement'
    _description = '新建报表'

    report_code = fields.Char(string='报表编号',required=True,size=4)
    report_name = fields.Char(string='报表名称',required=True)
    category = fields.Selection([
        ('1', '月报表'),
        ('2', '年报表'),
        ('3', '日报表'),
        ('4', '季报表'),
    ], string="编报类型",default='1',required=True)
    title_rows = fields.Integer(string="标题行数",default=3)
    head_rows = fields.Integer(string="表头行数",default=1)
    body_rows = fields.Integer(string="表体行数",default=30)
    tail_rows = fields.Integer(string="表尾行数",default=2)
    total_cols = fields.Integer(string="总列数",default=10)

    @api.multi
    def new_statement(self):
        currentdate = datetime.today().strftime("%Y-%m-%d")
        period_record_ids = self.env['ps.account.period'].get_period(currentdate)
        if period_record_ids == False:
            raise ValidationError('没有找到对应的会计期间，请首先到财务会计中维护会计期间！')
        if len(period_record_ids) > 1:
            raise ValidationError('找到多个会计期间，请先调整期间！')
        # fyearperiod:该年度的值为当前会计年度，会计区间是当前区间
        fyear = period_record_ids[0].year
        fperiod = period_record_ids[0].period
        fyearperiod = fyear + fperiod

        code = ""
        name = ""
        currentdate = fyearperiod
        category = "1"
        titlerows = 3
        headrows = 1
        bodyrows = 30
        tailrows = 2
        bodycols = 10

        if self.report_code:
            code = self.report_code
        else:
            raise ValidationError('报表编号不允许为空，请检查！')
        if self.report_name:
            name = self.report_name
        else:
            raise ValidationError('报表名称不允许为空，请检查！')
        if self.category:
            category = self.category
        else:
            category = "1"
        if self.title_rows:
            titlerows = self.title_rows
        else:
            titlerows = 3
        if self.head_rows:
            headrows = self.head_rows
        else:
            headrows = 1
        if self.body_rows:
            bodyrows = self.body_rows
        else:
            bodyrows = 30
        if self.tail_rows:
            tailrows = self.tail_rows
        else:
            tailrows = 2
        if self.total_cols:
            bodycols = self.total_cols
        else:
            bodycols = 10

        return {
            'type': 'ir.actions.client',
            'tag': 'statements',
            'context': {'isnew' : '1',
                        'report_code' : code,
                        'report_name' : name,
                        'report_date' : currentdate,
                        'category' : category,
                        'titlerows' : titlerows,
                        'headrows' : headrows,
                        'bodyrows' : bodyrows,
                        'tailrows' : tailrows,
                        'bodycols' : bodycols,
                        },
        }