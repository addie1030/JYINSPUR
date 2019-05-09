# -*- coding: utf-8 -*-

from odoo import models, fields, api

class statement_base(models.Model):
    _name = 'ps.statement.base'
    _description = 'ps.statement.base'

# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _
import time
from datetime import timedelta, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError,Warning
import json
from odoo import tools
from lxml import etree


class statement(models.Model):
    _name = 'ps.statement.statements'
    _description = "中国报表"

    company_id = fields.Many2one('res.company', string='公司', required=True,default=lambda self: self.env.user.company_id)
    report_code = fields.Char(string="报表编号",required=True,help="默认4位报表编号，最长20位，不支持特殊字符")
    # report_date = fields.Char(String="报表日期",Default=datetime.today().strftime("%Y-%m-%d"),Requird=True,help="6位年月日期，例如201801")
    # report_date = fields.Date(default=fields.Date.context_today,String="报表日期",Requird=True,help="6位年月日期，例如201801")
    report_date = fields.Char(string="报表日期", required=True, help="6位年月日期，例如201801")
    report_name = fields.Char(string="报表名称",required=True,help="最长255位")
    report_format = fields.Text(string="报表格式",required=True,help="")
    category = fields.Selection([
            ('1', '月报表'),
            ('2', '年报表'),
            ('3', '日报表'),
            ('4', '季报表'),
        ],string="编报类型",required=True)
    report_type = fields.Char(string="报表类型",default='1',required=True)
    title_rows = fields.Integer(string="标题行数",required=True)
    head_rows = fields.Integer(string="表头行数",required=True)
    body_rows = fields.Integer(string="表体行数",required=True)
    tail_rows = fields.Integer(string="表尾行数", required=True)
    total_rows = fields.Integer(string="总行数",required=True)
    total_cols = fields.Integer(string="总列数",required=True)
    isuse = fields.Char(string="使用中",default='0',required=True)
    isarchive = fields.Char(string="是否封存",Ddefaultefault='0',required=True)
    isissued = fields.Char(string="是否下发",default='0',required=True)
    iscurrentfiscalyear = fields.Char(string="是否当前会计年度报表",default='1',required=True)
    modelname = fields.Char(string="当前模块", default='ps_account', required=True)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
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

        record_ids = self.search([('report_date', '=', '000000')])
        for line in record_ids:
            if line:
                res = line.write({'report_date': fyearperiod})
                if not res:
                    raise ValidationError('更新报表会计区间报错，请检查！')
                jsonStr = line.report_format
                companysrc = "浪潮集团"
                companydes = self.env.user.company_id.name
                jsonStr = jsonStr.replace(companysrc, companydes)
                datesrc = "2018年05月"
                datedes = fyear + "年" + fperiod + "月"
                jsonStr = jsonStr.replace(datesrc, datedes)
                res = line.write({'report_format': jsonStr})
                if not res:
                    raise ValidationError('更新报表格式报错，请检查！')

        row_record_ids = self.env['ps.statement.sheet.rows'].search([('report_date', '=', '000000')])
        for line in row_record_ids:
            if line:
                res = line.write({'report_date': fyearperiod})
                if not res:
                    raise ValidationError('更新报表会计区间报错，请检查！')

        col_record_ids = self.env['ps.statement.sheet.columns'].search([('report_date', '=', '000000')])
        for line in col_record_ids:
            if line:
                res = line.write({'report_date': fyearperiod})
                if not res:
                    raise ValidationError('更新报表会计区间报错，请检查！')

        cell_record_ids = self.env['ps.statement.sheet.cells'].search([('report_date', '=', '000000')])
        for line in cell_record_ids:
            if line:
                res = line.write({'report_date': fyearperiod})
                if not res:
                    raise ValidationError('更新报表会计区间报错，请检查！')
        return super(statement, self).search_read(domain, fields, offset, limit, order)

    @api.model
    def get_reportproperties_params(self,code,date):
        properties_ids = self.search([('report_code', '=', code),('report_date', '=', date)])
        #properties_ids存放所有的数据表，按照"日期，编号"进行分组排序
        result = []
        for line in properties_ids:
            properties = {}
            properties['id'] = line['id']
            properties['report_code'] = line['report_code']
            properties['report_date'] = line['report_date']
            properties['report_name'] = line['report_name']
            properties['title_rows'] = line['title_rows']
            properties['head_rows'] = line['head_rows']
            properties['body_rows'] = line['body_rows']
            properties['tail_rows'] = line['tail_rows']
            properties['total_rows'] = line['total_rows']
            properties['total_cols'] = line['total_cols']
            result.append(properties)

        return result

    @api.model
    #从前端获取表格属性的信息, fe shorts for frontend.
    def get_reportproperties_from_frontend(self,code,date,name,tirows,hrows,brows,tarows,torows,tocols):
        if code:
            fereportcode = code
        else:
            raise ValidationError("传递的报表编号为空，请检查！")

        if date:
            fereportdate = date
        else:
            raise ValidationError("传递的报表日期为空，请检查！")
        torows2 = int(tirows) + int(hrows) + int(brows) + int(tarows)
        if torows != str(torows2):
            raise ValidationError("报表属性出现问题，请检查！")
        # 使用SQL语句修改数据库
        # self._cr.execute("update ps_statement_statements set report_name=%s,title_rows=%s where report_code='"+code+"' and report_date='"+date+"'",(name,tirows,))
        # report_name=%s中的%s，为括号内对应第一个参数，此处为(name,tirows,)里的names；
        # 想要在此执行SQL语句，一定要注意变量的写法(字符串的拼接)，双引号与引号的使用
        new_tableproperty = self.env['ps.statement.statements'].search([('report_code', '=', code),('report_date', '=', date)])
        new_tableproperty.write({'report_name': name})
        new_tableproperty.write({'title_rows': tirows})
        new_tableproperty.write({'head_rows': hrows})
        new_tableproperty.write({'body_rows': brows})
        new_tableproperty.write({'tail_rows': tarows})
        new_tableproperty.write({'total_rows': torows2})
        new_tableproperty.write({'total_cols': tocols})
        # fereportname = new_tableproperty["report_name"]
        # fereporttitlerows = new_tableproperty["title_rows"]
        # fereportheadrows = new_tableproperty["head_rows"]
        # fereportbodyrows = new_tableproperty["body_rows"]
        # fereporttailrows = new_tableproperty["tail_rows"]
        # fereporttotalrows = new_tableproperty["total_rows"]
        # fereporttotalcols = new_tableproperty["total_cols"]
        # checkstatus = True

    @api.multi
    @api.depends('report_name', 'report_code', 'report_date')
    def name_get(self):
        result = []
        for line in self:
            name = line.report_code + '#' + line.report_name + '#' + line.report_date
            result.append((line.id, name))
        return result

    @api.model
    def get_fiscalperiod(self):
        currentdate = datetime.today().strftime("%Y-%m-%d")
        period_record_ids = self.env['ps.account.period'].get_period(currentdate)
        if period_record_ids == False:
            # raise ValidationError('没有找到对应的会计期间，请首先到财务会计中维护会计期间！')
            return False
        if len(period_record_ids) > 1:
            raise ValidationError('找到多个会计期间，请先调整期间！')
        # fyearperiod:该年度的值为当前会计年度，会计区间是当前区间
        fyear = period_record_ids[0].year
        fperiod = period_record_ids[0].period
        fyearperiod = fyear + fperiod

        record_ids = self.search([('report_date', '=','000000')])
        for line in record_ids:
            if line:
                res = line.write({'report_date': fyearperiod})
                if not res:
                    raise ValidationError('更新报表会计区间报错，请检查！')
                jsonStr = line.report_format
                companysrc = "浪潮集团"
                companydes = self.env.user.company_id.name
                jsonStr = jsonStr.replace(companysrc, companydes)
                datesrc = "2018年05月"
                datedes = fyear + "年" + fperiod + "月"
                jsonStr = jsonStr.replace(datesrc, datedes)
                res = line.write({'report_format': jsonStr})
                if not res:
                    raise ValidationError('更新报表格式报错，请检查！')

        row_record_ids = self.env['ps.statement.sheet.rows'].search([('report_date', '=','000000')])
        for line in row_record_ids:
            if line:
                res = line.write({'report_date': fyearperiod})
                if not res:
                    raise ValidationError('更新报表会计区间报错，请检查！')

        col_record_ids = self.env['ps.statement.sheet.columns'].search([('report_date', '=','000000')])
        for line in col_record_ids:
            if line:
                res = line.write({'report_date': fyearperiod})
                if not res:
                    raise ValidationError('更新报表会计区间报错，请检查！')

        cell_record_ids = self.env['ps.statement.sheet.cells'].search([('report_date', '=','000000')])
        for line in cell_record_ids:
            if line:
                res = line.write({'report_date': fyearperiod})
                if not res:
                    raise ValidationError('更新报表会计区间报错，请检查！')

        return fyearperiod

    @api.model
    def get_statement_company(self):
        return self.env.user.company_id.name

    # @api.model
    # def delete_statements(self, record_ids):
    # while len(record_ids) > 0:
    #     id = record_ids.pop(0)
    #
    #     line = self.search([('id', '=', id)])
    @api.multi
    def unlink(self):
        for line in self:
            if line:
                reportcode = line.report_code
                reportdate = line.report_date
            else:
                break

            # 删除单元格信息
            cellline_ids = self.env['ps.statement.sheet.cells'].search([('report_code', '=',reportcode),('report_date', '=',reportdate)])
            if cellline_ids:
                for cellline in cellline_ids:
                    cellline.unlink()
            # 删除行信息
            rowline_ids = self.env['ps.statement.sheet.rows'].search([('report_code', '=',reportcode),('report_date', '=',reportdate)])
            if rowline_ids:
                for rowline in rowline_ids:
                    rowline.unlink()
            # 删除列信息
            colline_ids = self.env['ps.statement.sheet.columns'].search([('report_code', '=',reportcode),('report_date', '=',reportdate)])
            if colline_ids:
                for colline in colline_ids:
                    colline.unlink()
            # 删除报表信息
            # line.unlink()
        res = super(statement, self).unlink()
        return res

    @api.model
    def get_statement(self, code, date):
        if code is None:
            raise ValidationError('传递的报表编号参数为空，请检查！')
        if date is None:
            raise ValidationError('传递的报表会计区间参数为空，请检查！')
        line = self.search([('report_code', '=', code),('report_date', '=',date)])
        archive = "0"
        if line:
            jsonStr = line.report_format
            archive = line.isarchive
        else:
            jsonStr = ""

        # 同步获取单元格公式
        celldatasets = []
        formulas_ids = self.env['ps.statement.sheet.cells'].search(
            [('report_code', '=', code),
             ('report_date', '=', date),
             ('cell_formula', '!=', '')])
        if formulas_ids:
            for record in formulas_ids:
                celldata = {}
                if record.row_order == "" or record.row_order is None:
                    continue
                if record.col_order == "" or record.col_order is None:
                    continue
                # 去掉等号
                if record.cell_formula[1:] == "" or record.cell_formula[1:] is None:
                    formula = ""
                else:
                    formula = record.cell_formula[1:]

                if formula == "":
                    continue

                celldata["row"] = record.row_order
                celldata["col"] = record.col_order
                celldata["rowoffset"] = record.cell_rowoffset
                celldata["coloffset"] = record.cell_coloffset
                celldata["data"] = record.numerical_data
                celldata["text"] = record.character_data
                celldata["formula"] = formula

                formulas = {}  # 单元格公式
                operators = []  # 每一个单元格公式所包含的所有四则远算符号
                formulaunit = []  # 每一个单元格公式所包含的所有原子公式
                formulaunitbak = []  # 每一个单元格公式所包含的所有原子公式

                self.env['ps.statement.sheet.cells'].get_formula_from_arithmetic(formula, formulas, formulaunit, operators)
                celldata["formulaitems"] = formulaunit  # 四则运算的分解公式
                celldata["formulaoperators"] = operators  # 四则运算的运算符

                celldata["formulaitemscalculated"] = []
                celldata["formulaitemsvalue"] = []
                for iitem in range(len(formulaunit)):
                    celldata["formulaitemscalculated"].append(0)
                for iitem in range(len(formulaunit)):
                    celldata["formulaitemsvalue"].append(0)
                operators = []
                self.env['ps.statement.sheet.cells'].get_formula_from_arithmetic(formula, formulas, formulaunitbak, operators)
                celldata["formulaitemsbak"] = formulaunitbak  # 四则运算的分解公式备份

                celldatasets.append(celldata)

        colproperties = []
        columns_ids = self.env['ps.statement.sheet.columns'].search(
            [('report_code', '=', code),
             ('report_date', '=', date)])

        if columns_ids:
            for record in columns_ids:
                column = {}
                column["report_code"] = record.report_code
                column["report_date"] = record.report_date
                column["col_order"] = record.col_order
                column["col_coordinate"] = record.col_coordinate
                column["col_name"] = record.col_name
                column["col_isadjust"] = record.col_isadjust
                column["col_isamount"] = record.col_isamount
                column["col_isnumber"] = record.col_isnumber
                column["col_isitem"] = record.col_isitem
                colproperties.append(column)

        return [jsonStr,celldatasets,archive,colproperties]

    @api.model
    def get_statement_multimonth(self, code, date, months):
        result = []
        for month in months:
            monthjson = {}
            jsonStr = ""
            if month > 9:
                currentdate = date[0:4] + str(month)
            else:
                currentdate = date[0:4] + '0' + str(month)
            if code is None:
                continue
            if currentdate is None:
                continue

            line = self.search([('report_code', '=', code),('report_date', '=',currentdate)])
            if line:
                jsonStr = line.report_format

            monthjson["month"] = month
            monthjson["json"] = jsonStr

            result.append(monthjson)

        return result

    @api.model
    def save(self, code, name, date , category , titlerows , headrows ,bodyrows ,tailrows ,bodycols ,jsonstr, celldatasets,colsproperties):
        # 策略是先删除后插入
        modelname = 'ps_account'
        line = self.search([('report_code', '=', code), ('report_date', '=', date)])
        res = True
        columns = []
        if line:
            reportid = line.id
            report_type = line.report_type
            isarchive = line.isarchive
            isissued = line.isissued
            iscurrentfiscalyear = line.iscurrentfiscalyear
            modelname = line.modelname
            pivot_ids = self.env['ps.statement.pivot'].search([('report_code', '=', reportid)])
            rows_ids = self.env['ps.statement.sheet.rows'].search([('report_code', '=', code), ('report_date', '=', date)])
            colmuns_ids = self.env['ps.statement.sheet.columns'].search([('report_code', '=', code), ('report_date', '=', date)])
            for colline in colmuns_ids:
                column = {}
                column["id"] = colline.id
                column["col_order"] = colline.col_order
                column["col_coordinate"] = colline.col_coordinate
                column["col_name"] = colline.col_name
                column["col_isnumber"] = colline.col_isnumber
                column["col_isamount"] = colline.col_isamount
                column["col_isadjust"] = colline.col_isadjust
                column["col_isitem"] = colline.col_isitem
                columns.append(column)

            line.unlink() #已经重写该函数，处理删除行列单元格信息
        else:
            report_type = '1'
            isarchive = '0'
            isissued = '0'
            iscurrentfiscalyear = '1'

        # 插入ps.statement.statements记录
        if category == 'month':
            category = '1'
        if category == 'year':
            category = '2'
        if category == 'day':
            category = '3'
        if category == 'quarter':
            category = '4'
        maxid = self.create({
            'company_id': self.env.user.company_id.id,
            'report_code': code,
            'report_date': date,
            'report_name': name,
            'report_format': jsonstr,
            'category': category,
            'report_type': report_type,
            'title_rows': int(titlerows),
            'head_rows' : int(headrows),
            'body_rows': int(bodyrows),
            'tail_rows': int(tailrows),
            'total_rows': int(titlerows)+int(headrows)+int(bodyrows)+int(tailrows),
            'total_cols': int(bodycols),
            'isuse': '0',
            'isarchive': isarchive,
            'isissued': isissued,
            'iscurrentfiscalyear': iscurrentfiscalyear,
            'modelname': modelname,
        })

        # 插入ps.statement.sheet.rows记录
        total_rows = int(titlerows)+int(headrows)+int(bodyrows)+int(tailrows)
        rowid = 1
        while rowid <= total_rows:
            maxid = self.env['ps.statement.sheet.rows'].create({
                'report_code': code,
                'report_date': date,
                'row_order': rowid,
                'row_coordinate': rowid,
            })
            if maxid:
                rowid = rowid + 1
            else:
                raise ValidationError('插入报表行信息出错，请检查！')
                res = False
                break
        # 插入ps.statement.sheet.columns记录
        # total_cols = int(bodycols)
        # colid = 1
        # while colid <= total_cols:
        #     if columns:
        #         for colline in columns:
        #             if colline["col_order"] == str(colid):
        #                 col_name = colline["col_name"]
        #                 col_isnumber = colline["col_isnumber"]
        #                 col_isamount = colline["col_isamount"]
        #                 col_isadjust = colline["col_isadjust"]
        #                 col_isitem = colline["col_isitem"]
        #                 break
        #     else:
        #         col_name = ''
        #         col_isnumber = '0'
        #         col_isamount = '0'
        #         col_isadjust = '0'
        #         col_isitem = '0'
        #     maxid = self.env['ps.statement.sheet.columns'].create({
        #         'report_code': code,
        #         'report_date': date,
        #         'col_order': colid,
        #         'col_coordinate': colid,
        #         'col_name': col_name,
        #         'col_isnumber': col_isnumber,
        #         'col_isamount': col_isamount,
        #         'col_isadjust': col_isadjust,
        #         'col_isitem': col_isitem,
        #     })
        #     if maxid:
        #         colid = colid + 1
        #     else:
        #         raise ValidationError('插入报表列信息出错，请检查！')
        #         res = False
        #         break

        if colsproperties:
            colid = 1
            for colline in colsproperties:
                report_code = colline["report_code"]
                # report_date = colline["report_date"]
                report_date = date
                col_name = colline["col_name"]
                col_isnumber = colline["col_isnumber"]
                col_isamount = colline["col_isamount"]
                col_isadjust = colline["col_isadjust"]
                col_isitem = colline["col_isitem"]

                maxid = self.env['ps.statement.sheet.columns'].create({
                    'report_code': report_code,
                    'report_date': report_date,
                    'col_order': colid,
                    'col_coordinate': colid,
                    'col_name': col_name,
                    'col_isnumber': col_isnumber,
                    'col_isamount': col_isamount,
                    'col_isadjust': col_isadjust,
                    'col_isitem': col_isitem,
                })
                if maxid:
                    colid = colid + 1
                else:
                    raise ValidationError('插入报表列信息出错，请检查！')
                    res = False
                    break
        # 插入ps.statement.sheet.cells记录
        # 保存公式还未处理完善，需要先确定公式如何保存，使用model保存，而不是控件的格式，因为公式不识别
        # formulas中保存所有新定义的公式
        # 因为是新增报表，所以直接插入

        if celldatasets:
            index = 1
            for cellline in celldatasets:
                formula = cellline["formula"]
                formulaitems = cellline["formulaitems"]
                row = cellline["row"]
                col = cellline["col"]
                rowoffset = cellline["rowoffset"]
                coloffset = cellline["coloffset"]
                text = cellline["text"]
                data = cellline["data"]
                if formula:
                    if formula[0:1] != "=":
                        formula = "=" + formula
                else:
                    formula = ""
                maxid = self.env['ps.statement.sheet.cells'].create({
                    'report_code': code,
                    'report_date': date,
                    'cell_order': str(index),
                    'row_order': row,
                    'col_order': col,
                    'precision': 2,
                    'character_data': text,
                    'numerical_data': data,
                    'cell_isprotect': '0',
                    'cell_rowoffset': rowoffset,
                    'cell_coloffset': coloffset,
                    'cell_formula': formula,
                    'formula_type': '0',
                    'formula_level': '0',
                })
                if not maxid:
                    raise ValidationError('插入报表单元格信息出错，请检查！')
                    res = False
                    break
                else:
                    index = index + 1
                # 将四则运算公式拆分成原子公式
                if not formulaitems:
                    formulas = {}  # 单元格公式
                    operators = []  # 每一个单元格公式所包含的所有四则远算符号
                    formulaunit = []  # 每一个单元格公式所包含的所有原子公式
                    formulaunitbak = []  # 每一个单元格公式所包含的所有原子公式

                    self.env['ps.statement.sheet.cells'].get_formula_from_arithmetic(cellline["formula"], formulas, formulaunit,
                                                                                     operators)
                    cellline["formulaitems"] = formulaunit  # 四则运算的分解公式
                    cellline["formulaoperators"] = operators  # 四则运算的运算符

                    cellline["formulaitemscalculated"] = []
                    cellline["formulaitemsvalue"] = []
                    for iitem in range(len(formulaunit)):
                        cellline["formulaitemscalculated"].append(0)
                    for iitem in range(len(formulaunit)):
                        cellline["formulaitemsvalue"].append(0)
                    operators = []
                    self.env['ps.statement.sheet.cells'].get_formula_from_arithmetic(cellline["formula"], formulas, formulaunitbak,
                                                                                     operators)
                    cellline["formulaitemsbak"] = formulaunitbak  # 四则运算的分解公式备份
        return [res,celldatasets]

    # 计算多报表
    @api.model
    def calculate_multi(self, record_ids):
        while len(record_ids) > 0:
            id = record_ids.pop(0)

            line = self.search([('id', '=', id)])
            if line:
                code = line.report_code
                date = line.report_date
                jsonstr = line.report_format
                self.calculate(code, date, jsonstr)

    @api.model
    def getdata(self, code, date):
        # sql = """
        #             SELECT * FROM ps_statement_statements where report_code = '""" +code + """' and report_date = '""" + date + """'
        #         """
        # self.env.cr.execute(sql)
        # temps = self.env.cr.fetchall()
        line = self.env['ps.statement.statements'].search([('report_code', '=', code), ('report_date', '=', date)])
        temps = {}
        if line:
            temps["report_code"] = code
            temps["report_date"] = date
            temps["category"] = line.category
            temps["title_rows"] = line.title_rows
            temps["head_rows"] = line.head_rows
            temps["body_rows"] = line.body_rows
            temps["tail_rows"] = line.tail_rows
            temps["total_cols"] = line.total_cols

        return temps

    #计算单报表
    @api.model
    def calculate(self, code, date, celldatasets, state):
        line = self.env['ps.statement.statements'].search([('report_code', '=', code),('report_date', '=',date)])
        if line:
            resjosn = self.env['ps.statement.sheet.cells'].sudo().calculate_cells(code, date, celldatasets, state)
            if resjosn:
                res = resjosn
            else:
                res = ""
        else:
            res = ""
        return res

    @api.model
    def monthend(self, record_ids):
        endyear = False
        currentyeartemp = ""
        nextyeartemp = ""
        modelname = "ps_account"
        while len(record_ids) > 0:
            id = record_ids.pop(0)

            line = self.search([('id', '=', id)])
            if line:
                code = line.report_code
                currentdate = line.report_date
                currentyear = currentdate[0:4]
                currentmonth = currentdate[4:6]

                if currentmonth == "12":
                    nextyear = str(int(currentyear)+1)
                    nextmonth = "01"
                    endyear = True
                else:
                    nextyear = currentyear
                    nextmonth = str(int(currentmonth)+1)
                    if int(nextmonth) < 10:
                        nextmonth = "0"+str(nextmonth)

                nextdate = nextyear + nextmonth

                # #当前会计区间已知，推下一个会计区间，并且判断是否是年结
                # period_ids = self.env['ps.account.period'].search([('year', '=', currentyear),('period', '=', nextmonth)])
                # if period_ids:
                #
                #
                # # 如果结转的时候，下一个月跟当前月的会计年度不同，那么需要将上个年度的所有报表的iscurrentfiscalyear标记置为0
                #
                # tempdate = datetime.today().strftime("%Y-%m-%d")
                # currentdatetemp = currentdate[0:4] + "-" + currentdate[4:6] + "-" + tempdate[8:10]
                #
                # current_ids = self.env['ps.account.period'].get_period(currentdatetemp)
                # if current_ids == False:
                #     raise ValidationError('没有找到对应的会计期间，请首先到财务会计中维护会计期间！')
                # if len(current_ids) > 1:
                #     raise ValidationError('找到多个会计期间，请先调整期间！')
                # currnetyeartemp = current_ids[0].year
                #
                # nextdatetemp = nextdate[0:4] + "-" + nextdate[4:6] + "-" + tempdate[8:10]
                # next_ids = self.env['ps.account.period'].get_period(nextdatetemp)
                # if next_ids == False:
                #     raise ValidationError('没有找到对应的会计期间，请首先到财务会计中维护会计期间！')
                # if len(next_ids) > 1:
                #     raise ValidationError('找到多个会计期间，请先调整期间！')
                # # fyearperiod:该年度的值为当前会计年度，会计区间是当前区间
                # nextyeartemp = next_ids[0].year
                #
                # if currnetyeartemp != nextyeartemp:
                #     endyear = True

                # 如果下个月存在记录，那么先删除
                line = self.search([('report_code', '=', code), ('report_date', '=', nextdate)])
                if line:
                    line.unlink()

                # 插入记录
                linecurrentstatement = self.search([('report_code', '=', code), ('report_date', '=', currentdate)])
                if linecurrentstatement:
                    # sql = "SELECT MAX(id) FROM ps_statement_statements"
                    # self.env.cr.execute(sql)
                    # data_ids = self.env.cr.fetchone()
                    # maxid = data_ids[0] + 1

                    jsonStr = linecurrentstatement.report_format
                    datesrc = currentdate[0:4] + "年" + currentdate[4:6] + "月"
                    datedes = nextdate[0:4] + "年" + nextdate[4:6] + "月"
                    jsonStr = jsonStr.replace(datesrc, datedes)

                    maxid = self.create({
                        # 'id' : maxid,
                        'report_code': code,
                        'report_date': nextdate,
                        # 'company_id': line.company_id,
                        'report_name': linecurrentstatement.report_name,
                        'report_format': jsonStr,
                        'category': linecurrentstatement.category,
                        'report_type': linecurrentstatement.report_type,
                        'title_rows': linecurrentstatement.title_rows,
                        'head_rows': linecurrentstatement.head_rows,
                        'body_rows': linecurrentstatement.body_rows,
                        'tail_rows': linecurrentstatement.tail_rows,
                        'total_rows': linecurrentstatement.total_rows,
                        'total_cols': linecurrentstatement.total_cols,
                        'isuse': linecurrentstatement.isuse,
                        'isarchive': linecurrentstatement.isarchive,
                        'isissued': linecurrentstatement.isissued,
                        'iscurrentfiscalyear': '1',
                        'modelname': modelname,
                    })

                    # 处理行字典：先删后插
                    rows_ids = self.env['ps.statement.sheet.rows'].search(
                        [('report_code', '=', code), ('report_date', '=', nextdate)])
                    for rowline in rows_ids:
                        if rowline:
                            rowline.unlink()

                    rows_ids = self.env['ps.statement.sheet.rows'].search(
                        [('report_code', '=', code), ('report_date', '=', currentdate)])
                    for rowline in rows_ids:
                        if rowline:
                            maxid = self.env['ps.statement.sheet.rows'].create({
                                'report_code': code,
                                'report_date': nextdate,
                                'row_order': rowline.row_order,
                                'row_coordinate': rowline.row_coordinate,
                            })

                    # 处理列字典：先删后插
                    cols_ids = self.env['ps.statement.sheet.columns'].search(
                        [('report_code', '=', code), ('report_date', '=', nextdate)])
                    for colline in cols_ids:
                        if colline:
                            colline.unlink()
                    cols_ids = self.env['ps.statement.sheet.columns'].search(
                        [('report_code', '=', code), ('report_date', '=', currentdate)])
                    for colline in cols_ids:
                        if colline:
                            maxid = self.env['ps.statement.sheet.columns'].create({
                                'report_code': code,
                                'report_date': nextdate,
                                'col_order': colline.col_order,
                                'col_coordinate': colline.col_coordinate,
                                'col_name': colline.col_name,
                                'col_isnumber': colline.col_isnumber,
                                'col_isamount': colline.col_isamount,
                                'col_isadjust': colline.col_isadjust,
                                'col_isitem': colline.col_isitem,
                            })
                    # 处理单元格字典：先删后插
                    cells_ids = self.env['ps.statement.sheet.cells'].search(
                        [('report_code', '=', code), ('report_date', '=', nextdate)])
                    for cellline in cells_ids:
                        if cellline:
                            cellline.unlink()

                    cells_ids = self.env['ps.statement.sheet.cells'].search(
                        [('report_code', '=', code), ('report_date', '=', currentdate)])
                    for cellline in cells_ids:
                        if cellline:
                            maxid = self.env['ps.statement.sheet.cells'].create({
                                'report_code': code,
                                'report_date': nextdate,
                                'cell_order': cellline.cell_order,
                                'row_order': cellline.row_order,
                                'col_order': cellline.col_order,
                                'precision': cellline.precision,
                                'character_data': cellline.character_data,
                                'numerical_data': cellline.numerical_data,
                                'cell_isprotect': cellline.cell_isprotect,
                                'cell_rowoffset': cellline.cell_rowoffset,
                                'cell_coloffset': cellline.cell_coloffset,
                                'cell_formula': cellline.cell_formula,
                                'formula_type': cellline.formula_type,
                                'formula_level': cellline.formula_level,
                            })
            else:
                break

        if endyear:
            record_ids = self.search([('report_date', 'like', currnetyeartemp+'%')])
            if record_ids:
                for line in record_ids:
                    line.iscurrentfiscalyear = '0'
                    line.isarchive = '1'

        return {
            'type': 'ir.actions.act_window',
            'name': '财务报表',
            # 'view_id': self.env.ref('view_statement_statements_tree').id,
            'view_mode': 'tree',
            'res_model': 'ps.statement.statements',
            'target': 'current',
            'domain': [('iscurrentfiscalyear','=','1')]
        }
        # return maxid

    @api.model
    def archive(self, record_ids):
        while len(record_ids) > 0:
            id = record_ids.pop(0)

            line = self.search([('id', '=', id)])
            if line:
                line.isarchive = '1'

        return {
            'type': 'ir.actions.act_window',
            'name': '财务报表',
            # 'view_id': self.env.ref('view_statement_statements_tree').id,
            'view_mode': 'tree',
            'res_model': 'ps.statement.statements',
            'target': 'current',
            'domain': [('iscurrentfiscalyear', '=', '1')]
        }

    @api.model
    def unarchive(self, record_ids):
        while len(record_ids) > 0:
            id = record_ids.pop(0)

            line = self.search([('id', '=', id)])
            if line:
                line.isarchive = '0'

        return {
            'type': 'ir.actions.act_window',
            'name': '财务报表',
            # 'view_id': self.env.ref('view_statement_statements_tree').id,
            'view_mode': 'tree',
            'res_model': 'ps.statement.statements',
            'target': 'current',
            'domain': [('iscurrentfiscalyear', '=', '1')]
        }

    @api.model
    def datechange(self, code, date):
        line = self.search([('report_code', '=', code),('report_date', '=',date)])
        jsonStr = ""
        if line:
            jsonStr = line.report_format

        return jsonStr

    @api.model
    def menuedit_opening_sheet_action(self, param):
        # company = self.env.user.company_id
        if param == 'balancesheet':
            return {
                'type': 'ir.actions.client',
                'tag': 'balancesheet',
                'context' : {'report_code' : '0001','report_name' : '资产负债表'},
            }

        if param == 'incomestatement':
            return {
                'type': 'ir.actions.client',
                'tag': 'incomestatement',
            }

        if param == 'cashflowstatement':
            return {
                'type': 'ir.actions.client',
                'tag': 'cashflowstatement',
            }

    @api.model
    def monetaryunitadjust(self,code,date,monetaryunit):
        modelname = "ps_account"
        if code:
            if len(code) > 4:
                raise ValidationError('已经调整过，不允许再调整！')
                return False
            line = self.search([('report_code', '=', code + "_" + monetaryunit["code"]), ('report_date', '=', date)])
            if line:
                raise ValidationError('已经调整过，不允许再调整！')
                return False

            line = self.search([('report_code', '=', code), ('report_date', '=', date)])
            jsonStr = line.report_format
            reportname = line.report_name
            # jsonStr需要进行处理后再回填：第一步金额单位修改，第二步数值更新
            # 第一步金额单位修改
            if jsonStr.find('单位：元') > 0:
                jsonStr = jsonStr.replace('单位：元', '单位：' + monetaryunit["monetaryunit"])

            newreportname = reportname + "_" + monetaryunit["name"]
            if jsonStr.find(reportname) > 0:
                jsonStr = jsonStr.replace(reportname, newreportname)

            jsondic = json.loads(jsonStr)
            datatable = jsondic["sheets"][newreportname]["data"]["dataTable"]
            rowcount = jsondic["sheets"][newreportname]["rowCount"]
            columncount = jsondic["sheets"][newreportname]["columnCount"]
            # 第二步数值更新，找到数值列，将该列的所有内容更新
            cols_ids = self.env['ps.statement.sheet.columns'].search(
                [('report_code', '=', code), ('report_date', '=', date)])
            for colline in cols_ids:
                if colline:
                    col_order = colline.col_order
                    if colline.col_isadjust == '1':
                        for j in range(columncount):
                            if col_order == str(j + 1):
                                for i in range(rowcount):
                                    if str(i) not in datatable:
                                        continue
                                    if str(j) not in datatable[str(i)]:
                                        continue
                                    if "value" not in datatable[str(i)][str(j)]:
                                        continue
                                    if datatable[str(i)][str(j)]["value"] == 0 or datatable[str(i)][str(j)][
                                        "value"] is None:
                                        continue

                                    if type( datatable[str(i)][str(j)]["value"] ) == int:
                                        if monetaryunit["operator"] == '0':
                                            datatable[str(i)][str(j)]["value"] = str(float(datatable[str(i)][str(j)]["value"]) + monetaryunit["coefficient"])
                                        elif monetaryunit["operator"] == '1':
                                            datatable[str(i)][str(j)]["value"] = str(float(datatable[str(i)][str(j)]["value"]) - monetaryunit["coefficient"])
                                        elif monetaryunit["operator"] == '2':
                                            datatable[str(i)][str(j)]["value"] = str(float(datatable[str(i)][str(j)]["value"]) * monetaryunit["coefficient"])
                                        elif monetaryunit["operator"] == '3':
                                            datatable[str(i)][str(j)]["value"] = str(float(datatable[str(i)][str(j)]["value"]) / monetaryunit["coefficient"])
            jsondic["sheets"][newreportname]["data"]["dataTable"] = datatable
            jsonStr = json.dumps(jsondic)
            maxid = self.create({
                'report_code': code + "_" + monetaryunit["code"],
                'report_date': date,
                'report_name': line.report_name + "_" + monetaryunit["name"],
                'report_format': jsonStr,
                'category': line.category,
                'report_type': line.report_type,
                'title_rows': line.title_rows,
                'head_rows': line.head_rows,
                'body_rows': line.body_rows,
                'tail_rows': line.tail_rows,
                'total_rows': line.total_rows,
                'total_cols': line.total_cols,
                'isuse': line.isuse,
                'isarchive': line.isarchive,
                'isissued': line.isissued,
                'iscurrentfiscalyear': '1',
                'modelname': modelname,
            })

            rows_ids = self.env['ps.statement.sheet.rows'].search(
                [('report_code', '=', code), ('report_date', '=', date)])
            for rowline in rows_ids:
                if rowline:
                    maxid = self.env['ps.statement.sheet.rows'].create({
                        'report_code': code + "_" + monetaryunit["code"],
                        'report_date': date,
                        'row_order': rowline.row_order,
                        'row_coordinate': rowline.row_coordinate,
                    })

            # 处理列字典
            cols_ids = self.env['ps.statement.sheet.columns'].search(
                [('report_code', '=', code), ('report_date', '=', date)])
            for colline in cols_ids:
                if colline:
                    maxid = self.env['ps.statement.sheet.columns'].create({
                        'report_code': code + "_" + monetaryunit["code"],
                        'report_date': date,
                        'col_order': colline.col_order,
                        'col_coordinate': colline.col_coordinate,
                        'col_name': colline.col_name,
                        'col_isnumber': colline.col_isnumber,
                        'col_isamount': colline.col_isamount,
                        'col_isadjust': colline.col_isadjust,
                        'col_isitem': colline.col_isitem,
                    })
            # 处理单元格字典
            cells_ids = self.env['ps.statement.sheet.cells'].search(
                [('report_code', '=', code), ('report_date', '=', date)])
            for cellline in cells_ids:
                if cellline:
                    maxid = self.env['ps.statement.sheet.cells'].create({
                        'report_code': code + "_" + monetaryunit["code"],
                        'report_date': date,
                        'cell_order': cellline.cell_order,
                        'row_order': cellline.row_order,
                        'col_order': cellline.col_order,
                        'precision': cellline.precision,
                        'character_data': cellline.character_data,
                        'numerical_data': cellline.numerical_data,
                        'cell_isprotect': cellline.cell_isprotect,
                        'cell_rowoffset': cellline.cell_rowoffset,
                        'cell_coloffset': cellline.cell_coloffset,
                        'cell_formula': cellline.cell_formula,
                        'formula_type': cellline.formula_type,
                        'formula_level': cellline.formula_level,
                    })

        return True


class statement_rows(models.Model):
    _name = 'ps.statement.sheet.rows'
    _description = "财务报表行字典"

    report_code = fields.Char(String="报表编号",Requird=True)
    # report_date = fields.Char(String="报表日期",Default=fields.Datetime.now().strftime("%Y-%m-%d"),Requird=True)
    # report_date = fields.Date(default=fields.Date.context_today,String="报表日期",Requird=True,help="6位年月日期，例如201801")
    report_date = fields.Char(String="报表日期", Requird=True, help="6位年月日期，例如201801")
    row_order = fields.Char(String="行序号",Requird=True)
    row_coordinate = fields.Integer(String="行坐标",Requird=True)

class statement_columns(models.Model):
    _name = 'ps.statement.sheet.columns'
    _description = "财务报表列字典"

    report_code = fields.Char(String="报表编号",Requird=True)
    # report_date = fields.Char(String="报表日期",Default=fields.Datetime.now().strftime("%Y-%m-%d"),Requird=True)
    # report_date = fields.Date(default=fields.Date.context_today,String="报表日期",Requird=True,help="6位年月日期，例如201801")
    report_date = fields.Char(String="报表日期", Requird=True, help="6位年月日期，例如201801")
    col_order = fields.Char(String="列序号",Requird=True)
    col_coordinate = fields.Integer(String="列坐标",Requird=True)
    col_name = fields.Char(String="列名称",Requird=True)
    col_isnumber = fields.Char(String="数值列",Requird=True)
    col_isamount = fields.Char(String="汇总列",Requird=True)
    col_isadjust = fields.Char(String="调整列",Requird=True)
    col_isitem = fields.Char(String="项目列", Requird=True)

    @api.model
    def get_columns_info(self,code,date):#需要注释
        whole_ids = self.search([('report_code', '=', code),('report_date', '=', date)])
        code_set = set()
        code_list = []
        result = []
        for line in whole_ids:
            code = str(line["report_code"])
            code_set.add(code)
        for element in code_set:
            code_list.append(element)
            code_list.sort()
        date_set = set()
        date_list = []
        for line in whole_ids:
            date = str(line["report_date"])
            date_set.add(date)
        for element in date_set:
            date_list.append(element)
            date_list.sort()
        for i in date_list:
            for j in code_list:
                columns_ids = self.env['ps.statement.sheet.columns'].search(
                    [('report_code', '=', j), ('report_date', '=', i)])
                for row in columns_ids:
                    colproperties = {}
                    colproperties['id'] = row['id']
                    colproperties['report_code'] = row['report_code']
                    colproperties['report_date'] = row['report_date']
                    colproperties['col_order'] = row['col_order']
                    colproperties['col_name'] = row['col_name']
                    colproperties['col_isnumber'] = row['col_isnumber']
                    colproperties['col_isamount'] = row['col_isamount']
                    colproperties['col_isadjust'] = row['col_isadjust']
                    colproperties['col_isitem'] = row['col_isitem']
                    result.append(colproperties)
        return result

    @api.model
    #从前端获取表格属性的信息, fe shorts for frontend.
    def get_columnsproperties_from_frontend(self,code,date,colproperties):
        if code:
            code = code
        else:
            raise ValidationError("传递的报表编号为空，请检查！")
        if date:
            date = date
        else:
            raise ValidationError("传递的报表日期为空，请检查！")
        if colproperties:
            colproperties = colproperties
        else:
            raise ValidationError("传递的列属性为空，请检查！")
        col_properties = self.env['ps.statement.sheet.columns'].search([('report_code','=',code),('report_date','=',date)], order='id')
        for i in range(0,len(col_properties)):
            col_properties[i].write({'col_isnumber': str(colproperties[i]['col_isnumber'])})
            col_properties[i].write({'col_isamount': str(colproperties[i]['col_isamount'])})
            col_properties[i].write({'col_isadjust': str(colproperties[i]['col_isadjust'])})
            col_properties[i].write({'col_isitem': str(colproperties[i]['col_isitem'])})
            # col_properties[i]['col_isnumber'] = colproperties[i]['col_isnumber']

    @api.multi
    @api.depends('col_order')
    def name_get(self):
        result = []
        for line in self:
            col = self.env["ps.statement.sheet.cells"].colnum_to_name(line.col_coordinate - 1)
            name = line.report_code + '#' + line.report_date + '#' + line.col_name + '#' + col
            result.append((line.id, name))
        return result

class statement_cells(models.Model):
    _name = 'ps.statement.sheet.cells'
    _description = "财务报表单元字典"

    report_code = fields.Char(String="报表编号",Requird=True)
    # report_date = fields.Char(String="报表日期",Default=fields.Datetime.now().strftime("%Y-%m-%d"),Requird=True)
    # report_date = fields.Date(default=fields.Date.context_today,String="报表日期",Requird=True,help="6位年月日期，例如201801")
    report_date = fields.Char(String="报表日期", Requird=True, help="6位年月日期，例如201801")
    cell_order = fields.Char(String="单元序号", Requird=True)
    row_order = fields.Char(String="行序号",Requird=True)
    col_order = fields.Char(String="列序号", Requird=True)
    precision = fields.Integer(String="精度",Requird=False)
    character_data = fields.Char(String="文本数据", Requird=False)
    numerical_data = fields.Float(String="数值数据", Requird=False)
    cell_isprotect = fields.Char(String="是否保护", Requird=False)
    cell_rowoffset = fields.Integer(String="行位移", Requird=True)
    cell_coloffset = fields.Integer(String="列位移", Requird=True)
    cell_formula = fields.Char(String="公式", Requird=False)
    formula_type = fields.Char(String="公式标志", Requird=False)
    formula_level = fields.Integer(String="公式级别", Requird=True)

    def get_keyvalue_by_key(self, input_json, key, formulas):
        key_value = ''
        if isinstance(input_json, dict):
            for json_result in input_json.values():
                if key in input_json.keys():
                    key_value = input_json.get(key)
                else:
                    self.get_keyvalue_by_key(json_result, key,formulas)
        elif isinstance(input_json, list):
            for json_array in input_json:
                self.get_keyvalue_by_key(json_array, key,formulas)
        if key_value != '':
            print(str(key) + " = " + str(key_value))
            formulas[str(key_value)] = str(key_value)
        # return formulas

    def set_keyvalue_by_key(self, input_json, key, values):
        key_value = ''
        if isinstance(input_json, dict):
            for json_result in input_json.values():
                if key in input_json.keys():
                    key_value = input_json.get(key)
                    input_json['value'] = values[str(key_value)]
                else:
                    self.set_keyvalue_by_key(json_result, key, values)
        elif isinstance(input_json, list):
            for json_array in input_json:
                self.set_keyvalue_by_key(json_array, key, values)
        if key_value != '':
            print(str(key) + " = " + str(key_value))

    @api.model
    def save_cells(self, code, date, jsonstr, formulas):
        if jsonstr:
            #需要考虑插入行，插入列，删除行，删除列的情况20180713
            #插入行，插入列，删除行，删除列会影响BB取数公式的坐标
            row_ids = self.env['ps.statement.sheet.rows'].search([('report_code', '=', code), ('report_date', '=', date)])
            column_ids = self.env['ps.statement.sheet.columns'].search([('report_code', '=', code), ('report_date', '=', date)])

            res = True
        else:
            res = False
        return res

    @api.model
    def split_formula(self, formula, result):
        # KMJE(0, 0, "1001", "JFFS", "KMJS=1")
        if formula.find('(') > 0 :
            result['name'] = formula[0:formula.find('(')]
            parmstr = formula[formula.find('('):]
            parmstr = parmstr[1:len(parmstr)-1]
            count = 1
            while (parmstr.find(',') > 0):
                key = 'parm'+str(count)
                temp = parmstr[0:parmstr.find(',')]
                if temp[0:1] == '"':
                    temp = temp[1:]
                if temp[-1] == '"':
                    temp = temp[0:len(temp)-1]
                result[key] = temp
                parmstr = parmstr[parmstr.find(',')+1:]
                count = count + 1
            key = 'parm' + str(count)
            if parmstr[0:1] == '"':
                parmstr = parmstr[1:]
            if parmstr[-1] == '"':
                parmstr = temp[0:len(parmstr) - 1]
            result[key] = parmstr

    @api.model
    def colname_to_num(self, colname):
        if type(colname) is not str:
            return colname
        col = 0
        power = 1
        for i in range(len(colname) - 1, -1, -1):
            ch = colname[i]
            col += (ord(ch) - ord('A') + 1) * power
            power *= 26
        return col - 1

    @api.model
    def colnum_to_name(self, colnum):
        if type(colnum) != int:
            return colnum
        if colnum > 25:
            ch1 = chr(colnum % 26 + 65)
            ch2 = chr(colnum / 26 + 64)
            return ch2 + ch1
        else:
            return chr(colnum % 26 + 65)

    @api.model
    def get_calculate_formulas_sql(self, code, date, sql, celldatasets, state):
        if celldatasets:
            fyear = date[0:4]
            fperiod = date[4:6]
            fyearperiod = date

            # cfyearperiod:该年度的值为f_vkey='CW_KJND'的值，会计区间是第一个区间
            # 第一版使用01代替会计区间的第一个区间，待解决
            # currentfyear = self.env['ps.config'].sudo().get_param('cw_kjqj')
            currentfyear = self.env.user.company_id.ps_current_fiscalyear
            currentfyear = currentfyear[0:4]
            currentfirstperiod = '01'
            cfyearperiod = currentfyear + currentfirstperiod

            # prefyearperiod:该年度的值为当前会计年度的上一年度，会计区间是上一年度的最后一个区间
            # 第一版使用12代替会计区间的最后一个区间，待解决
            fyear = str(int(date[0:4]) - 1)
            fperiod = '12'
            prefyearperiod = fyear + fperiod

            # fyearfirstperiod:该年度的值为当前会计年度，会计区间是第一个区间
            # 第一版使用01代替会计区间的第一个区间，待解决
            fyear = date[0:4]
            fperiod = '01'
            fyearfirstperiod = fyear + fperiod

            # fyearpreperiod:该年度的值为当前会计年度，会计区间是上一个会计区间
            # 第一版使用01代替会计区间的第一个区间，待解决
            fyear = date[0:4]
            fperiod = date[4:6]
            if int(fperiod) > 10:
                fperiod = str(int(fperiod) - 1)
            else:
                fperiod = '0' + str(int(fperiod) - 1)
            fyearpreperiod = fyear + fperiod

            cfyearperiod = "'" + cfyearperiod + "'"
            fyearperiod = "'" + fyearperiod + "'"
            prefyearperiod = "'" + prefyearperiod + "'"
            fyearfirstperiod = "'" + fyearfirstperiod + "'"
            fyearpreperiod = "'" + fyearpreperiod + "'"

            bb_yjz = False
            # bb_yjz = self.env['ps.config'].sudo().get_param('bb_yjz')
            bb_yjz = self.env.user.company_id.ps_statement_calculation_contains_unaccounted
            sql = ""
            for cellline in celldatasets:
                formulaitems = cellline["formulaitems"]
                tempsql = ""
                if formulaitems:
                    for i in range(len(formulaitems)):
                        formula = formulaitems[i]
                        tempformula = "'" + formula + "'"
                        if formula:
                            result = {}
                            self.split_formula(formula, result)
                            if not result:
                                continue
                            if state == "NOTBB":
                                if result['name'].upper() == 'KMJE':
                                    line = self.env['ps.statement.formulas'].search(
                                        [('name', '=', result['name'].upper()),
                                         ('formula_object', '=', result['parm4'].upper())])

                                    accountid = result['parm3']
                                    if accountid.find(':') >= 0:
                                        saccountid = accountid[0:accountid.find(':')]
                                        eaccountid = accountid[accountid.find(':') + 1:]
                                    else:
                                        saccountid = accountid
                                        eaccountid = accountid + "z"

                                    saccountid = "'" + saccountid + "'"
                                    eaccountid = "'" + eaccountid + "'"

                                    formulayear = result['parm1']
                                    formulamonth = result['parm2']

                                    if formulayear == '0':
                                        year = date[0:4]
                                    else:
                                        year = str(int(date[0:4]) + int(formulayear))
                                    if formulamonth == '0':
                                        month = date[4:6]
                                    else:
                                        month = str(int(date[4:6]) + int(formulamonth))
                                    formulayearperiod = year + month

                                    formulayearperiod = "'" + formulayearperiod + "'"

                                    if result['parm4'].upper() == "JFYE":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            tempsql = tempsql.replace("#SPERIOD#", cfyearperiod)
                                            # tempsql = tempsql.replace("#EPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#EPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                            tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "NCJF":
                                        if line:
                                            if fyear <= currentfyear:
                                                tempsql = "select sum(account_move_line.debit)-sum(account_move_line.credit) as ye,#FORMULA# as formula,max(account_move.id) as id from account_move,account_move_line,account_account,ps_account_period A where account_move_line.account_id=account_account.id and account_move.id = account_move_line.move_id and account_move.ps_period_code = A.id and A.year||A.period = #SPERIOD# and account_move.name='00000' and account_move.ref='QC' and account_account.code >= #SACCOUNTCODE# and account_account.code <= #EACCOUNTCODE# group by account_account.code "

                                                tempsql = tempsql.replace("#FORMULA#", tempformula)
                                                tempsql = tempsql.replace("#SPERIOD#", cfyearperiod)
                                                tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                                tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)
                                                if sql == "":
                                                    sql = tempsql
                                                else:
                                                    sql = sql + " UNION ALL " + tempsql
                                            else:
                                                temp = line.formula_design
                                                tempsql = temp.encode('utf-8')
                                                tempsql = tempsql.decode('utf-8')
                                                # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                                formula_id = line.id
                                                parmline = self.env['ps.statement.formula.params'].search(
                                                    [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                                if parmline:
                                                    fields = parmline.param_value

                                                tempsql = tempsql.replace("#FIELDS#", fields)
                                                tempsql = tempsql.replace("#FORMULA#", tempformula)
                                                tempsql = tempsql.replace("#SPERIOD#", cfyearperiod)
                                                tempsql = tempsql.replace("#EPERIOD#", prefyearperiod)
                                                tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                                tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                                if bb_yjz == False:
                                                    temppos = tempsql.find('group by')
                                                    tempsql = tempsql[
                                                              0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                                 temppos:len(
                                                                                                                     tempsql)]

                                                if sql == "":
                                                    sql = tempsql
                                                else:
                                                    sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "JFFS":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            # tempsql = tempsql.replace("#SPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#SPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                            tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "JFLJ":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            tempsql = tempsql.replace("#SPERIOD#", fyearfirstperiod)
                                            # tempsql = tempsql.replace("#EPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#EPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                            tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "YCJF":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            tempsql = tempsql.replace("#SPERIOD#", cfyearperiod)
                                            tempsql = tempsql.replace("#EPERIOD#", fyearpreperiod)
                                            tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                            tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[0:temppos] + " AND account_move.state='posted' " +tempsql[temppos:len(tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "DFFS":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            # tempsql = tempsql.replace("#SPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#SPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                            tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "DFLJ":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            tempsql = tempsql.replace("#SPERIOD#", fyearfirstperiod)
                                            # tempsql = tempsql.replace("#EPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#EPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                            tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "NCDF":
                                        if line:
                                            if fyear <= currentfyear:
                                                tempsql = "select sum(account_move_line.credit)-sum(account_move_line.debit) as ye,#FORMULA# as formula,max(account_move.id) as id from account_move,account_move_line,account_account,ps_account_period A where account_move_line.account_id=account_account.id and account_move.id = account_move_line.move_id and account_move.ps_period_code = A.id and A.year||A.period = #SPERIOD# and account_move.name='00000' and account_move.ref='QC' and account_account.code >= #SACCOUNTCODE# and account_account.code <= #EACCOUNTCODE# group by account_account.code "

                                                tempsql = tempsql.replace("#FORMULA#", tempformula)
                                                tempsql = tempsql.replace("#SPERIOD#", cfyearperiod)
                                                tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                                tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                                if bb_yjz == False:
                                                    temppos = tempsql.find('group by')
                                                    tempsql = tempsql[
                                                              0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                                 temppos:len(
                                                                                                                     tempsql)]
                                                if sql == "":
                                                    sql = tempsql
                                                else:
                                                    sql = sql + " UNION ALL " + tempsql
                                            else:
                                                temp = line.formula_design
                                                tempsql = temp.encode('utf-8')
                                                tempsql = tempsql.decode('utf-8')
                                                # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                                formula_id = line.id
                                                parmline = self.env['ps.statement.formula.params'].search(
                                                    [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                                if parmline:
                                                    fields = parmline.param_value

                                                tempsql = tempsql.replace("#FIELDS#", fields)
                                                tempsql = tempsql.replace("#FORMULA#", tempformula)
                                                tempsql = tempsql.replace("#SPERIOD#", cfyearperiod)
                                                tempsql = tempsql.replace("#EPERIOD#", prefyearperiod)
                                                tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                                tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                                if bb_yjz == False:
                                                    temppos = tempsql.find('group by')
                                                    tempsql = tempsql[
                                                              0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                                 temppos:len(
                                                                                                                     tempsql)]

                                                if sql == "":
                                                    sql = tempsql
                                                else:
                                                    sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "DFYE":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            tempsql = tempsql.replace("#SPERIOD#", cfyearperiod)
                                            # tempsql = tempsql.replace("#EPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#EPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#SACCOUNTCODE#", saccountid)
                                            tempsql = tempsql.replace("#EACCOUNTCODE#", eaccountid)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                if result['name'].upper() == 'LLJE':
                                    line = self.env['ps.statement.formulas'].search(
                                        [('name', '=', result['name'].upper()),
                                         ('formula_object', '=', result['parm4'].upper())])

                                    item = result['parm3']
                                    item = "'" + item + "'"

                                    formulayear = result['parm1']
                                    formulamonth = result['parm2']

                                    if formulayear == '0':
                                        year = date[0:4]
                                    else:
                                        year = str(int(date[0:4]) + int(formulayear))
                                    if formulamonth == '0':
                                        month = date[4:6]
                                    else:
                                        month = str(int(date[4:6]) + int(formulamonth))
                                    formulayearperiod = year + month
                                    formulayearperiod = "'" + formulayearperiod + "'"

                                    if result['parm4'].upper() == "JFLJ":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            tempsql = tempsql.replace("#SPERIOD#", fyearfirstperiod)
                                            # tempsql = tempsql.replace("#EPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#EPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#CASHFLOWITEM#", item)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "DFLJ":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            tempsql = tempsql.replace("#SPERIOD#", fyearfirstperiod)
                                            # tempsql = tempsql.replace("#EPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#EPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#CASHFLOWITEM#", item)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "JFFS":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            # tempsql = tempsql.replace("#SPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#SPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#CASHFLOWITEM#", item)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    if result['parm4'].upper() == "DFFS":
                                        if line:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            # tempsql = temp.encode('unicode-escape').decode('string_escape')
                                            formula_id = line.id
                                            parmline = self.env['ps.statement.formula.params'].search(
                                                [('formula_id', '=', formula_id), ('name', '=', '#FIELDS#')])
                                            if parmline:
                                                fields = parmline.param_value

                                            tempsql = tempsql.replace("#FIELDS#", fields)
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            # tempsql = tempsql.replace("#SPERIOD#", fyearperiod)
                                            tempsql = tempsql.replace("#SPERIOD#", formulayearperiod)
                                            tempsql = tempsql.replace("#CASHFLOWITEM#", item)

                                            if bb_yjz == False:
                                                temppos = tempsql.find('group by')
                                                tempsql = tempsql[
                                                          0:temppos] + " AND account_move.state='posted' " + tempsql[
                                                                                                             temppos:len(
                                                                                                                 tempsql)]

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                            if state == "BB":
                                if result['name'].upper() == 'BB':
                                    # 如果是报表函数，那么需要首先检查该公式对应单元格中是否有公式，
                                    # 如果有公式，那么首先计算单元格中的公式，如果该单元格中的公式，仍然包含BB公式，那么继续检查BB公式对应的单元格，
                                    # 直到最终的单元格没有公式或者不存在BB公式为止，那么首先计算有公式但是没有包含BB公式的单元格，
                                    # 如果没有公式，那么直接单元格上的数据，如果没有数据，此时值为0，
                                    # 同时需要设置计算过标记和记录计算过的结果，下次不再计算直接取数
                                    # parm1:会计年度parm2:会计区间parm3:报表编号parm4:取数区间
                                    formulayear = result['parm1']
                                    formulamonth = result['parm2']
                                    formularcode = result['parm3']
                                    formularange = result['parm4']

                                    if formulayear == '0':
                                        year = date[0:4]
                                    else:
                                        year = str(int(date[0:4]) + int(formulayear))
                                    if formulamonth == '0':
                                        month = date[4:6]
                                    else:
                                        month = str(int(date[4:6]) + int(formulamonth))
                                    formulayearperiod = year + month

                                    if formularange.find(':') >= 0:
                                        startrange = formularange[0:formularange.find(':')]
                                        endrange = formularange[formularange.find(':') + 1:]
                                    else:
                                        startrange = formularange
                                        endrange = formularange

                                    temp = startrange[1:2]
                                    if temp.isdigit():
                                        rangesrow = int(startrange[1:]) - 1
                                        rangescol = self.colname_to_num(startrange[0:1])
                                    else:
                                        rangesrow = int(startrange[2:]) - 1
                                        rangescol = self.colname_to_num(startrange[0:2])

                                    temp = endrange[1:2]
                                    if temp.isdigit():
                                        rangeerow = int(endrange[1:]) - 1
                                        rangeecol = self.colname_to_num(endrange[0:1])
                                    else:
                                        rangeerow = int(endrange[2:]) - 1
                                        rangeecol = self.colname_to_num(endrange[0:2])

                                    if code[0:1] == "'" or code[0:1] == '"':
                                        reportcode = code
                                    else:
                                        reportcode = "'" + code + "'"
                                    formulayearperiod = "'" + formulayearperiod + "'"
                                    # 如果是报表编号为当前打开报表编号，报表会计区间是当前打开会计区间，那么当前表取数
                                    # 当前表取数使用控件自带公式，例如，=C5
                                    # 否则，由于前后端不一致的原因，BB公式只能通过SQL完成取当前报表的其他区间的数或者跨表取数
                                    # 前后端同步问题，已经解决，通过传递celldatasets，将前端数据传递到后端20180705
                                    # =BB(0,0,0001,C5)
                                    # C5单元格有公式=BB(0,0,0001,C6)

                                    # 计算逻辑遇到的问题20180707
                                    # 问题一：BB循环逻辑不对
                                    # 问题二：非BB公式计算完成后，回填表格时，有一种情况未考虑，单元格的公式为=KMJE+BB+KMJE的情况
                                    # =BB(0,0,0001,C6)+BB(0,0,0002,C6)+BB(0,0,0001,G6)
                                    # =BB(0,0,0001,C6:C7)
                                    line = self.env['ps.statement.formulas'].search([('name', '=', result['name'].upper())])

                                    if line:
                                        if formularcode == code and formulayearperiod == fyearperiod:
                                            # 将取当前报表数据的BB公式替换为控件的公式
                                            if formularange.find(':') >= 0:
                                                cellline["formulaitems"][i] = "SUM(" + formularange + ")"
                                            else:
                                                cellline["formulaitems"][i] = formularange
                                        else:
                                            temp = line.formula_design
                                            tempsql = temp.encode('utf-8')
                                            tempsql = tempsql.decode('utf-8')
                                            tempsql = tempsql.replace("#FORMULA#", tempformula)
                                            tempsql = tempsql.replace("#REPORTCODE#", reportcode)
                                            tempsql = tempsql.replace("#REPORTDATE#", formulayearperiod)
                                            tempsql = tempsql.replace("#STARTROW#", str(rangesrow))
                                            tempsql = tempsql.replace("#ENDROW#", str(rangescol))
                                            tempsql = tempsql.replace("#STARTCOL#", str(rangeerow))
                                            tempsql = tempsql.replace("#ENDCOL#", str(rangeecol))

                                            if sql == "":
                                                sql = tempsql
                                            else:
                                                sql = sql + " UNION ALL " + tempsql
                                    else:
                                        if sql == "":
                                            sql = tempsql
                                        else:
                                            sql = sql + " UNION ALL " + tempsql
                        else:
                            if tempsql == "":
                                continue
                            else:
                                if sql == "":
                                    sql = tempsql
                                else:
                                    sql = sql + " UNION ALL " + tempsql
                else:
                    if tempsql == "":
                        continue
                    else:
                        if sql == "":
                            sql = tempsql
                        else:
                            sql = sql + " UNION ALL " + tempsql
        else:
            sql = ""
        return sql

    @api.model
    def get_formula_from_arithmetic(self, formula, formulas, formulaunit, operators):
        # formulas = {}  # 单元格公式
        # operaters = []  # 每一个单元格公式所包含的所有四则远算符号
        # formulaunit = []  # 每一个单元格公式所包含的所有原子公式
        while (formula.find('+') > 0 or formula.find('-') > 0 or formula.find('*') > 0 or formula.find('/') > 0):
            posplus = formula.find('+')
            posminus = formula.find('-')
            posmultiply = formula.find('*')
            posdivide = formula.find('/')

            # temp = {}
            # temp["operator"] = ""
            # temp["pos"] = 0
            # if posplus >= 0:
            #     temp["operator"] = "+"
            #     temp["pos"] = posplus
            # if posminus >= 0:
            #     if posminus < temp:
            #         temp["operator"] = "-"
            #         temp["pos"] = posminus
            # if posmultiply >= 0:
            #     if posmultiply < temp:
            #         temp["operator"] = "*"
            #         temp["pos"] = posmultiply
            # if posdivide >= 0:
            #     if posdivide < temp:
            #         temp["operator"] = "/"
            #         temp["pos"] = posdivide
            #
            # operators.append(temp["operator"])

            w = []
            if posplus >= 0:
                w.append(posplus)
                # operators.append('+')
            if posminus >= 0:
                w.append(posminus)
                # operators.append('-')
            if posmultiply >= 0:
                w.append(posmultiply)
                # operators.append('*')
            if posdivide >= 0:
                w.append(posdivide)
                # operators.append('/')

            w.sort()

            if posplus == w[0]:
                tempformula = formula[0:formula.find('+')]
                formula = formula[formula.find('+') + 1:]
                formulas[tempformula] = tempformula
                formulaunit.append(tempformula)
                operators.append('+')
            if posminus == w[0]:
                tempformula = formula[0:formula.find('-')]
                formula = formula[formula.find('-') + 1:]
                formulas[tempformula] = tempformula
                formulaunit.append(tempformula)
                operators.append('-')
            if posmultiply == w[0]:
                tempformula = formula[0:formula.find('*')]
                formula = formula[formula.find('*') + 1:]
                formulas[tempformula] = tempformula
                formulaunit.append(tempformula)
                operators.append('*')
            if posdivide == w[0]:
                tempformula = formula[0:formula.find('/')]
                formula = formula[formula.find('/') + 1:]
                formulas[tempformula] = tempformula
                formulaunit.append(tempformula)
                operators.append('/')

        formulas[formula] = formula
        formulaunit.append(formula)

        result = []
        result.append(formulas)
        result.append(formulaunit)
        result.append(operators)

        return result

    @api.model
    def formula_by_rowcol_change(self, code, date, celldatasets, defineformulas, insertrows, insertcols, deleterows, deletecols):
        # if not celldatasets:
        #     raise ValidationError('该报表单元格信息为空，请检查。')

        currentdate = datetime.today().strftime("%Y-%m-%d")
        period_record_ids = self.env['ps.account.period'].get_period(currentdate)
        if period_record_ids == False:
            raise ValidationError('没有找到对应的会计期间，请先维护期间！')
        if len(period_record_ids) > 1:
            raise ValidationError('找到多个会计期间，请先调整期间！')
        # fyearperiod:该年度的值为当前会计年度，会计区间是当前区间
        fyear = period_record_ids[0].year
        fperiod = period_record_ids[0].period
        fyearperiod = fyear + fperiod

        # 插入行
        if insertrows:
            for iinsertrow in range(len(insertrows)):
                insertrow = insertrows[iinsertrow]["row"]
                insertcount = insertrows[iinsertrow]["count"]
                for cellline in celldatasets:
                    formulaitems = cellline["formulaitems"]
                    if formulaitems:
                        # 将插入行以后的所有公式调整坐标
                        row = int(cellline["row"])
                        if row >= insertrow:
                            cellline["row"] = str(row + 1)
                        for i in range(len(formulaitems)):
                            formula = formulaitems[i]
                            if formula:
                                result = {}
                                self.split_formula(formula, result)
                                if not result:
                                    continue
                                if result['name'].upper() == 'BB':
                                    formulayear = result['parm1']
                                    formulamonth = result['parm2']
                                    formularcode = result['parm3']
                                    formularange = result['parm4']

                                    if formulayear == '0':
                                        year = date[0:4]
                                    else:
                                        year = str(int(date[0:4]) + int(formulayear))
                                    if formulamonth == '0':
                                        month = date[4:6]
                                    else:
                                        month = str(int(date[4:6]) + int(formulamonth))
                                    formulayearperiod = year + month

                                    if formularange.find(':') >= 0:
                                        startrange = formularange[0:formularange.find(':')]
                                        endrange = formularange[formularange.find(':') + 1:]
                                    else:
                                        startrange = formularange
                                        endrange = formularange

                                    temp = startrange[1:2]
                                    if temp.isdigit():
                                        rangesrow = int(startrange[1:]) - 1
                                        rangescol = self.colname_to_num(startrange[0:1])
                                    else:
                                        rangesrow = int(startrange[2:]) - 1
                                        rangescol = self.colname_to_num(startrange[0:2])

                                    temp = endrange[1:2]
                                    if temp.isdigit():
                                        rangeerow = int(endrange[1:]) - 1
                                        rangeecol = self.colname_to_num(endrange[0:1])
                                    else:
                                        rangeerow = int(endrange[2:]) - 1
                                        rangeecol = self.colname_to_num(endrange[0:2])

                                    if formularcode == code and formulayearperiod == fyearperiod:
                                        if insertrow <= rangesrow:
                                            rangesrow = rangesrow + 1
                                            rangeerow = rangeerow + 1

                                        if insertrow > rangesrow and insertrow < rangeerow:
                                            rangeerow = rangeerow + 1

                                        # 将增加后的行坐标转换成公式的坐标
                                        descstartrange = ""
                                        descendrange = ""
                                        temp = startrange[1:2]
                                        if temp.isdigit():
                                            descstartrange = startrange[0:1]+str(rangesrow)
                                        else:
                                            descstartrange = startrange[0:2] + str(rangesrow)

                                        temp = endrange[1:2]
                                        if temp.isdigit():
                                            descendrange = endrange[0:1]+str(rangeerow)
                                        else:
                                            descendrange = endrange[0:2] + str(rangeerow)

                                        descrange = ""
                                        if formularange.find(':') >= 0:
                                            descrange = descstartrange+":"+descendrange
                                        else:
                                            descrange = descstartrange

                                        formula = formula.replace(formularange, descrange)
                                        cellline["formulaitems"][i] = formula
        # 插入列
        if insertcols:
            for iinsertcol in range(len(insertcols)):
                insertcol = insertcols[iinsertcol]["col"]
                insertcount = insertcols[iinsertcol]["count"]
                for cellline in celldatasets:
                    formulaitems = cellline["formulaitems"]
                    if formulaitems:
                        # 将插入列以后的所有公式调整坐标
                        col = int(cellline["col"])
                        if col >= insertcol:
                            cellline["col"] = str(col + 1)
                        for i in range(len(formulaitems)):
                            formula = formulaitems[i]
                            if formula:
                                result = {}
                                self.split_formula(formula, result)
                                if not result:
                                    continue
                                if result['name'].upper() == 'BB':
                                    formulayear = result['parm1']
                                    formulamonth = result['parm2']
                                    formularcode = result['parm3']
                                    formularange = result['parm4']

                                    if formulayear == '0':
                                        year = date[0:4]
                                    else:
                                        year = str(int(date[0:4]) + int(formulayear))
                                    if formulamonth == '0':
                                        month = date[4:6]
                                    else:
                                        month = str(int(date[4:6]) + int(formulamonth))
                                    formulayearperiod = year + month

                                    if formularange.find(':') >= 0:
                                        startrange = formularange[0:formularange.find(':')]
                                        endrange = formularange[formularange.find(':') + 1:]
                                    else:
                                        startrange = formularange
                                        endrange = formularange

                                    temp = startrange[1:2]
                                    if temp.isdigit():
                                        rangesrow = int(startrange[1:]) - 1
                                        rangescol = self.colname_to_num(startrange[0:1])
                                    else:
                                        rangesrow = int(startrange[2:]) - 1
                                        rangescol = self.colname_to_num(startrange[0:2])

                                    temp = endrange[1:2]
                                    if temp.isdigit():
                                        rangeerow = int(endrange[1:]) - 1
                                        rangeecol = self.colname_to_num(endrange[0:1])
                                    else:
                                        rangeerow = int(endrange[2:]) - 1
                                        rangeecol = self.colname_to_num(endrange[0:2])

                                    if formularcode == code and formulayearperiod == fyearperiod:
                                        if insertcol <= rangescol:
                                            rangescol = rangescol + 1
                                            rangeecol = rangeecol + 1

                                        if insertcol > rangescol and insertcol < rangeecol:
                                            rangeecol = rangeecol + 1

                                        # 将增加后的列坐标转换成公式的坐标
                                        descstartrange = ""
                                        descendrange = ""
                                        descstartrange = self.colnum_to_name(rangescol)+str(rangesrow)
                                        descendrange = self.colnum_to_name(rangeecol) + str(rangeerow)

                                        descrange = ""
                                        if formularange.find(':') >= 0:
                                            descrange = descstartrange+":"+descendrange
                                        else:
                                            descrange = descstartrange

                                        formula = formula.replace(formularange, descrange)
                                        cellline["formulaitems"][i] = formula
        # 删除行
        if deleterows:
            for iideleterow in range(len(deleterows)):
                deleterow = deleterows[iideleterow]["row"]
                deletecount = deleterows[iideleterow]["count"]

                for n in range(deleterow, deleterow + deletecount):
                    for i in range(len(celldatasets) - 1, -1, -1):
                        if int(celldatasets[i]["row"]) == n:
                            celldatasets.pop(i)

                    for cellline in celldatasets:
                        formulaitems = cellline["formulaitems"]
                        row = int(cellline["row"])
                        # 将删除行以后的所有公式调整坐标
                        if row > n:
                            if formulaitems:
                                cellline["row"] = str(row - 1)

        # 删除列
        if deletecols:
            for iideletecol in range(len(deletecols)):
                deletecol = deletecols[iideletecol]["col"]
                deletecount = deletecols[iideletecol]["count"]
                for n in range(deletecol, deletecol + deletecount):
                    for i in range(len(celldatasets) - 1, -1, -1):
                        if int(celldatasets[i]["col"]) == n:
                            celldatasets.pop(i)
                    for cellline in celldatasets:
                        formulaitems = cellline["formulaitems"]
                        col = int(cellline["col"])
                        # 将删除行以后的所有公式调整坐标
                        if col > n:
                            if formulaitems:
                                cellline["col"] = str(col - 1)

        return celldatasets


    @api.model
    def calculate_cells(self, code, date, celldatasets, state):
        # 分解公式
        if celldatasets:
            for j in range(len(celldatasets)):
                formula = celldatasets[j]["formula"]
                if formula:
                    formulas = {}  # 单元格公式
                    operators = []  # 每一个单元格公式所包含的所有四则远算符号
                    formulaunit = []  # 每一个单元格公式所包含的所有原子公式
                    formulaunitbak = []  # 每一个单元格公式所包含的所有原子公式
                    self.get_formula_from_arithmetic(formula, formulas, formulaunit, operators)
                    celldatasets[j]["formulaitems"] = formulaunit       # 四则运算的分解公式
                    celldatasets[j]["formulaoperators"] = operators     # 四则运算的运算符
                    if len(celldatasets[j]["formulaitemscalculated"]) == 0:
                        for iitem in range(len(formulaunit)):
                            celldatasets[j]["formulaitemscalculated"].append(0)
                    if len(celldatasets[j]["formulaitemsvalue"]) == 0:
                        for iitem in range(len(formulaunit)):
                            celldatasets[j]["formulaitemsvalue"].append(0)
                    operators = []
                    self.get_formula_from_arithmetic(formula, formulas, formulaunitbak, operators)
                    celldatasets[j]["formulaitemsbak"] = formulaunitbak  # 四则运算的分解公式备份

        sql = ""
        sql = self.get_calculate_formulas_sql(code, date, sql, celldatasets, state)
        if sql == "" or sql is None:
            # raise ValidationError('没有形成正确的取数SQL语句，请检查是否存在公式。')
            if state == "BB":
                return celldatasets
            else:
                return False

        self.env['ps.statement.calculate.temptable'].table_create(sql)
        # balance_ids = self.env['ps.statement.calculate.temptable'].search([], order=False)
        sql = "select ye,formula from ps_statement_calculate_temptable"
        self.env.cr.execute(sql)
        balance_ids = []
        balance_ids = self.env.cr.fetchall()

        celldatasetsbak = []

        if balance_ids is None or len(balance_ids) <= 0:
            for cellline in celldatasets:
                if cellline["formula"]:
                    cellline["data"] = 0
                celldatasetsbak.append(cellline)
        if len(balance_ids) > 0:
            for cellline in celldatasets:
                formulaitems = cellline["formulaitems"]
                for iitem in range(len(formulaitems)):
                    for record in balance_ids:
                        if formulaitems[iitem] == record[1]:
                            cellline["formulaitemsvalue"][iitem] = record[0]
                            cellline["formulaitemscalculated"][iitem] = 1

                celllinebak = {}
                formulaitemsvalue = []
                formulaoperators = []
                celllinebak["formula"] = cellline["formula"]

                for valueindex in range(len(cellline["formulaitemsvalue"])):
                    formulaitemsvalue.append(cellline["formulaitemsvalue"][valueindex])
                celllinebak["formulaitemsvalue"] = formulaitemsvalue

                for operatorindex in range(len(cellline["formulaoperators"])):
                    formulaoperators.append(cellline["formulaoperators"][operatorindex])
                celllinebak["formulaoperators"] = formulaoperators

                celldatasetsbak.append(celllinebak)

                tempvalueleft = 0
                if len(cellline["formulaitemsvalue"]) > 0:
                    tempvalueleft = cellline["formulaitemsvalue"].pop(0)
                    while len(cellline["formulaitemsvalue"]) > 0:
                        valueright = cellline["formulaitemsvalue"].pop(0)
                        if len(cellline["formulaoperators"]) > 0:
                            operator = cellline["formulaoperators"].pop(0)
                        else:
                            operator = ''
                        if operator == '+':
                            tempvalueleft = tempvalueleft + valueright
                        elif operator == '-':
                            tempvalueleft = tempvalueleft - valueright
                        elif operator == '*':
                            tempvalueleft = tempvalueleft * valueright
                        elif operator == '/':
                            tempvalueleft = tempvalueleft / valueright

                    cellline["data"] = tempvalueleft

        for cellline in celldatasets:
            for celllinebak in celldatasetsbak:
                if cellline["formula"] == celllinebak["formula"]:
                    cellline["formulaitemsvalue"] = celllinebak["formulaitemsvalue"]
                    cellline["formulaoperators"] = celllinebak["formulaoperators"]

        return celldatasets

    @api.model
    def get_cells_info(self, code, date):
        if code:
            report_code = code
        else:
            raise ValidationError('传递的报表编号为空，请检查！')

        if date:
            report_date = date
        else:
            raise ValidationError('传递的报表日期为空，请检查！')

        cells_ids = self.search([('report_code', '=', report_code), ('report_date', '=', report_date)], order='row_order,col_order')
        result = []
        for line in cells_ids:
            cells = {}
            cells['report_code'] = line['report_code']
            cells['report_date'] = line['report_date']
            cells['cell_order'] = line['cell_order']
            cells['row_order'] = line['row_order']
            cells['col_order'] = line['col_order']
            cells['precision'] = str(line['precision'])
            cells['character_data'] = line['character_data']
            cells['numerical_data'] = str(line['numerical_data'])
            cells['cell_isprotect'] = line['cell_isprotect']
            cells['cell_rowoffset'] = str(line['cell_rowoffset'])
            cells['cell_coloffset'] = str(line['cell_coloffset'])
            cells['cell_formula'] = line['cell_formula']
            cells['formula_type'] = line['formula_type']
            cells['formula_level'] = str(line['formula_level'])
            result.append(cells)

        return result

    @api.model
    def get_cell_formula(self,code,date,rowid,colid):
        if code:
            report_code = code
        else:
            raise ValidationError('传递的报表编号为空，请检查！')

        if date:
            report_date = date
        else:
            raise ValidationError('传递的报表日期为空，请检查！')

        cells_ids = self.search([('report_code', '=', report_code), ('report_date', '=', report_date),('row_order', '=', rowid), ('col_order', '=', colid)], order='row_order,col_order')
        result = []
        for line in cells_ids:
            cells = {}
            cells['cell_formula'] = line['cell_formula']
            result.append(cells)

        return result

    @api.model
    def set_cell_formula(self, code, date, rowid, colid, rowoffset, coloffset, formula):
        # rowoffset = rowoffset - 1
        # coloffset = coloffset - 1
        line = self.search([('report_code', '=', code), ('report_date', '=', date), ('row_order', '=', rowid), ('col_order', '=', colid)])
        if line:
            linerowoffset = line["cell_rowoffset"]
            linecoloffset = line["cell_coloffset"]

            if linerowoffset == rowoffset and linecoloffset == coloffset:
                line["cell_formula"] = formula
                return 1
            else:
                line.unlink()

        maxcellorder = "0"
        cells_ids = self.search([('report_code', '=', code), ('report_date', '=', date)])
        cellorders = []
        if cells_ids:
            for line in cells_ids:
                temp = line['cell_order']
                cellorders.append(int(temp))
            maxcellorder = max(cellorders)

        maxcellorder = str(int(maxcellorder) + 1)
        maxid = self.create({
            'report_code': code,
            'report_date': date,
            'cell_order': maxcellorder,
            'row_order': rowid,
            'col_order': colid,
            'precision': 2,
            'character_data': '',
            'numerical_data': 0,
            'cell_isprotect': '0',
            'cell_rowoffset': rowoffset,
            'cell_coloffset': coloffset,
            'cell_formula': formula,
            'formula_type': '0',
            'formula_level': '0',
        })
        return maxid

    @api.model
    def delete_cell_formula(self,code,date,rowid,colid):
        if code:
            report_code = code
        else:
            raise ValidationError('删除单元格公式时，传递的报表编号为空，请检查！')

        if date:
            report_date = date
        else:
            raise ValidationError('删除单元格公式时，传递的报表日期为空，请检查！')

        cells_ids = self.search([('report_code', '=', report_code), ('report_date', '=', report_date),('row_order', '=', rowid), ('col_order', '=', colid)], order='row_order,col_order')
        result = True
        for line in cells_ids:
            result = line.unlink()

        return result

class statement_month_end(models.Model):
    _name = 'ps.statement.month.end'
    _description = "财务报表月结信息"

    tablename = fields.Char(String="表名", Requird=True)
    isdateflag = fields.Char(String="月份相关", Requird=True)
    datefield = fields.Char(String="月份列名", Requird=False)

class statement_year_end(models.Model):
    _name = 'ps.statement.year.end'
    _description = "财务报表年结信息"

    tablename = fields.Char(String="表名", Requird=True)
    isdateflag = fields.Char(String="月份相关", Requird=True)
    datefield = fields.Char(String="月份列名", Requird=False)
    endflag = fields.Char(String="年结标志", Requird=False)

class statement_formulas(models.Model):
    _name = "ps.statement.formulas"
    _description = "财务报表公式字典"

    # formula_id = fields.Char(String="公式编号", Requird=True)
    name = fields.Char(String="公式名称", Requird=True, translate=True)
    formula_summary = fields.Char(String="公式描述", Requird=False, translate=True)
    formula_object = fields.Char(String="取数对象", Requird=False)
    formula_design = fields.Char(String="公式模型", Requird=False, Help="双#号定义参数，例如，#ACCOUNT#")
    formula_type = fields.Selection([
        ('0', '系统'),
        ('1', '自定义'),
    ], String="公式类型", Requird=True, default='1')
    formula_scope = fields.Selection([
        ('0', '单元公式'),
        ('1', '区域公式'),
    ], String="作用范围", Requird=True, default='0')
    formula_note = fields.Char(String="备注", Requird=False, translate=True)
    formula_params_ids = fields.One2many('ps.statement.formula.params', 'formula_id', String='公式参数')


    # @api.onchange('formula_design')
    # def onchange_formula_design(self):
    # onchange方式在后台已经插入数据，但是前台不显示，所以使用按钮方式
    @api.onchange('formula_design')
    def onchange_formula_design(self):
        if self.formula_design:
            warning = {
                'title': _('提示信息'),
                'message': _('公式模型已经改变，需要点击“生成公式参数”重新生成公式参数。'),
            }
            return {'warning': warning}

    # @api.model
    def create_params(self):
        result = {}
        params = []
        if self.formula_design:
            formula = self.formula_design
            if formula.find('#') > 0:
                parmstr = formula[formula.find('#')+1:]
                count = 1
                while (parmstr.find('#') > 0):
                    key = 'param' + str(count)
                    temp = parmstr[0:parmstr.find('#')]
                    result[key] = '#' + temp + '#'
                    parmstr = parmstr[parmstr.find('#') + 1:]
                    parmstr = parmstr[parmstr.find('#') + 1:]
                    count = count + 1
        else:
            raise ValidationError('参数来源于公式模型，请首先维护公式模型。')
        if len(result) > 0:
            index = 1
            period_obj = self.env['ps.statement.formula.params']
            record_ids = period_obj.search([('formula_id','=',self.id)])
            if record_ids:
                for record in record_ids:
                    record.unlink()
            record_ids = period_obj.search([('formula_id','=',False)])
            if record_ids:
                for record in record_ids:
                    record.unlink()
            while index <= len(result):
                param = result['param'+str(index)]
                period_obj.create({
                    'formula_id': self.id,
                    'param_id': "{:0>4d}".format(index),
                    'name': param,
                    'param_description': "参数"+str(index),
                    # 'param_value': code,
                    # 'param_sysvar': nextdate,
                    'param_category': '0',
                    'param_type': 'C',
                    # 'param_note': line.row_coordinate,
                })
                params.append({
                    'formula_id': self.id,
                    'param_id': "{:0>4d}".format(index),
                    'name': param,
                    'param_description': "参数"+str(index),
                    # 'param_value': code,
                    # 'param_sysvar': nextdate,
                    'param_category': '0',
                    'param_type': 'C',
                    # 'param_note': line.row_coordinate,
                })
                index = index + 1

        return params
    @api.model
    def get_formulas(self):
        formulas_ids = self.search([('formula_type', '=', '1')],order='name')
        result = []
        for line in formulas_ids:
            formulas = {}
            formulas['id'] = line['id']
            formulas['name'] = line['name']
            formulas['formula_summary'] = line['formula_summary']
            formulas['formula_object'] = line['formula_object']
            formulas['formula_design'] = line['formula_design']
            formulas['formula_type'] = line['formula_type']
            formulas['formula_scope'] = str(line['formula_scope'])
            formulas['formula_note'] = line['formula_note']
            result.append(formulas)

        return result

    def get_formula_name(self):
        formulas_ids = self.search([],order='name')
        result = []
        for line in formulas_ids:
            result.append(line['name'])

        return result

    # def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    #     if context is None: context = {}
    #     view_id = 'view_statement_formulas_form'
    #     res = super(statement_formulas, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
    #     if res['type'] == "form":
    #         id = res['id']
    #         if self.formula_type == '0':
    #             doc = etree.XML(res['arch'])
    #             doc.xpath("//form")[0].set("edit", "false")
    #             res['arch'] = etree.tostring(doc)
    #     return res



    # @api.model
    # def create(self, vals):
    #     if not vals.get('formula_id'):
    #         vals['formula_id'] = self.env['ir.sequence'].next_by_code('ps.statement.formulas') or '/'
    #         print(vals['formula_id'])
    #     return super(statement_formulas, self).create(vals)

class statement_system_variables(models.Model):
    _name = "ps.statement.system.variables"
    _description = "财务报表系统变量字典"

    name = fields.Char(String="名称", Requird=True)
    description = fields.Char(String="描述", Requird=True)
    note = fields.Char(String="备注", Requird=True)

class statement_formula_params(models.Model):
    _name = "ps.statement.formula.params"
    _description = "财务报表公式参数字典"

    # formula_id = fields.Char(String="公式编号", Requird=True)
    formula_id = fields.Many2one('ps.statement.formulas', String='公式编号')
    param_id = fields.Char(String="参数序号", Requird=True)
    name = fields.Char(String="参数名称", Requird=False)
    param_description = fields.Char(String="参数描述", Requird=False)
    param_value = fields.Char(String="参数值", Requird=False)
    # param_sysvar = fields.Selection([
    #     ('@YEAR@', '会计年，2018'),
    #     ('@MONTH@', '会计月，01'),
    #     ('@DAY@', '会计日，01'),
    #     ('@FDATE@', '会计日期，20180101'),
    #     ('@LDATE@', '登录日期，20180101'),
    #     ('@COMPANY@', '单位名称'),
    #     ('@COMPANYID@', '单位编号'),
    # ], String="系统变量", Requird=True, default='@YEAR@')
    param_sysvar = fields.Selection(selection='_list_system_variables',String="系统变量")
    param_category = fields.Selection([
        ('0', '手工录入'),
        ('1', '表格取数'),
        ('2', '系统参数'),
    ], String="来源方式", Requird=True, default='0')
    param_type = fields.Selection([
        ('C', '字符型'),
        ('N', '数值型'),
        ('B', '布尔型'),
    ], String="参数类型", Requird=True, default='C')
    param_note = fields.Char(String="备注", Requird=False)

    @api.model
    def _list_system_variables(self):
        self._cr.execute("SELECT name, description FROM ps_statement_system_variables ORDER BY name")
        return self._cr.fetchall()
    @api.model
    def get_formula_params(self):
        formulas_ids = self.env["ps.statement.formulas"].search([('formula_type', '=', '1')], order='name')
        if formulas_ids:
            for formula in formulas_ids:
                params_ids = self.search([('formula_id', '=', formula.id)], order='formula_id,param_id')
                result = []
                for line in params_ids:
                    params = {}
                    params['formula_id'] = line['formula_id']
                    params['param_id'] = line['param_id']
                    params['name'] = line['name']
                    params['param_description'] = line['param_description']
                    params['param_value'] = line['param_value']
                    params['param_sysvar'] = line['param_sysvar']
                    params['param_category'] = line['param_category']
                    params['param_type'] = line['param_type']
                    params['param_note'] = line['param_note']
                    result.append(params)
        else:
            result = []

        return result

class statement_function(models.Model):
    _name = "ps.statement.functions"
    _description = "财务报表函数"

    name = fields.Char(String="公式名称", Requird=True, translate=True)
    func_summary = fields.Char(String="公式描述", Requird=False, translate=True)
    func_design = fields.Char(String="公式模型", Requird=False, Help="双#号定义参数，例如，#ACCOUNT#")
    func_type = fields.Selection([
        ('0', '系统'),
        ('1', '自定义'),
    ], String="公式类型", Requird=True, default='1')
    func_scope = fields.Selection([
        ('0', '单元公式'),
        ('1', '区域公式'),
    ], String="作用范围", Requird=True, default='0')
    func_note = fields.Char(String="备注", Requird=False)
    func_params_ids = fields.One2many('ps.statement.function.params', 'func_id', String='公式参数')

    @api.model
    def get_functions(self):
        functions_ids = self.search([],order='name')
        result = []
        for line in functions_ids:
            functions = {}
            functions['id'] = line['id']
            functions['name'] = line['name']
            functions['func_summary'] = line['func_summary']
            functions['func_design'] = line['func_design']
            functions['func_type'] = line['func_type']
            functions['func_scope'] = str(line['func_scope'])
            functions['func_note'] = line['func_note']
            result.append(functions)

        return result

    def get_function_name(self):
        functions_ids = self.search([],order='name')
        result = []
        for line in functions_ids:
            result.append(line['name'])

        return result

class statement_function_params(models.Model):
    _name = "ps.statement.function.params"
    _description = "财务报表函数参数"

    func_id = fields.Many2one('ps.statement.functions', String='公式编号')
    param_id = fields.Char(String="参数序号", Requird=True)
    name = fields.Char(String="参数名称", Requird=False)
    param_description = fields.Char(String="参数描述", Requird=False)
    param_value = fields.Char(String="参数值", Requird=False)
    param_sysvar = fields.Selection(selection='_list_system_variables',String="系统变量")
    param_category = fields.Selection([
        ('0', '手工录入'),
        ('1', '表格取数'),
        ('2', '系统参数'),
    ], String="来源方式", Requird=True, default='0')
    param_type = fields.Selection([
        ('C', '字符型'),
        ('N', '数值型'),
        ('B', '布尔型'),
    ], String="参数类型", Requird=True, default='C')
    param_note = fields.Char(String="备注", Requird=False)

    @api.model
    def get_function_params(self):
        params_ids = self.search([], order='func_id,param_id')
        result = []
        for line in params_ids:
            params = {}
            params['func_id'] = line['func_id']
            params['param_id'] = line['param_id']
            params['name'] = line['name']
            params['param_description'] = line['param_description']
            params['param_value'] = line['param_value']
            params['param_sysvar'] = line['param_sysvar']
            params['param_category'] = line['param_category']
            params['param_type'] = line['param_type']
            params['param_note'] = line['param_note']
            result.append(params)

        return result

    @api.model
    def _list_system_variables(self):
        self._cr.execute("SELECT name, description FROM ps_statement_system_variables ORDER BY name")
        return self._cr.fetchall()

class statement_monetaryunit_define(models.Model):
    _name = "ps.statement.monetaryunit.define"
    _description = "金额单位定义"

    code = fields.Char(String="调整编号", Requird=True)
    name = fields.Char(String="调整名称", Requird=True)
    operator = fields.Selection([
        ('0', '+'),
        ('1', '-'),
        ('2', '*'),
        ('3', '/'),
    ], String="调整符号", Requird=True, default='0')
    coefficient = fields.Integer(String="调整系数", Requird=True, Default=1000)
    precision = fields.Integer(String="调整精度", Requird=True, Default=2)
    monetaryunit = fields.Char(String="金额单位", Requird=True)

    @api.model
    def get_monetaryunit(self):
        monetaryunit_ids = self.search([])
        result = []
        for line in monetaryunit_ids:
            monetaryunits = {}
            monetaryunits['id'] = line['id']
            monetaryunits['code'] = line['code']
            monetaryunits['name'] = line['name']
            monetaryunits['operator'] = line['operator']
            monetaryunits['coefficient'] = line['coefficient']
            monetaryunits['precision'] = line['precision']
            monetaryunits['monetaryunit'] = line['monetaryunit']
            result.append(monetaryunits)

        return result

class statement_pivot_define(models.Model):
    _name = "ps.statement.pivot"
    _description = "数据透视表"

    # report_code = fields.Many2one('ps.statement.statements', String='报表编号')
    # report_code = fields.Selection(selection='_list_all_statements', string='报表编号', required=True)
    report_code = fields.Char(string='报表编号', required=True)
    code = fields.Char(string="透视编号", required=True)
    name = fields.Char(string="透视名称", required=True)
    pivot_details_ids = fields.One2many('ps.statement.pivot.details', 'pivot_id', string='透视定义')

    @api.model
    def default_get(self, fields):
        pivot_ids = self.search([('report_code','=',self._context.get("report_code"))])
        temp = "0"
        for line in pivot_ids:
            if int(line.code) > int(temp):
                temp = line.code

        if int(temp) > 8:
            temp = str(int(temp) + 1)
        else:
            temp = "0"+str(int(temp) + 1)
        defaults = super(statement_pivot_define, self).default_get(fields)
        defaults['report_code'] = self._context.get("report_code")
        defaults['code'] = temp
        return defaults

    @api.model
    def _list_all_statements(self):
        report_code = self._context.get("report_code")
        currentdate = self._context.get("report_date")
        self._cr.execute("SELECT report_code, report_name FROM ps_statement_statements WHERE report_code = '"+ report_code +"' AND report_date = '"+currentdate+"'  ORDER BY report_code")
        return self._cr.fetchall()

    @api.model
    def get_pivottable(self,code,date):
        pivottable_ids = self.search([])
        # line = self.env['ps.statement.statements'].search([('report_code', '=', code),('report_date', '=',date)])
        # if line:
        #     reportid = line.id
        tables = []
        for line in pivottable_ids:
            pivottables = {}
            if code == line['report_code']:
                pivottables['id'] = line['id']
                pivottables['report_code'] = line['report_code']
                pivottables['code'] = line['code']
                pivottables['name'] = line['name']
                tables.append(pivottables)

        details = []
        for line in tables:
            detail_ids = self.env['ps.statement.pivot.details'].search([('pivot_id', '=', line['id'])])
            for detailline in detail_ids:
                pivotdetails = {}
                pivotdetails['pivot_id'] = detailline['pivot_id'].id
                pivotdetails['detail_id'] = detailline['detail_id']
                pivotdetails['col_order'] = detailline['col_order']
                pivotdetails['col_name'] = detailline['col_name']
                pivotdetails['col_type'] = detailline['col_type']
                pivotdetails['access_coord'] = detailline['access_coord']
                details.append(pivotdetails)

        return [tables,details]

    def create_details(self):
        if self.report_code:
            currentdate = self._context.get("report_date")
            query = "SELECT col_order,col_name,col_isnumber FROM ps_statement_sheet_columns WHERE report_code = '"+self.report_code+"' AND report_date='"+currentdate+"'"
            self._cr.execute(query)
            res = self._cr.fetchall()
        else:
            raise ValidationError('报表编号为空，请检查。')
        if res:
            detail_obj = self.env['ps.statement.pivot.details']
            record_ids = detail_obj.search([('pivot_id','=',self.id)])
            if record_ids:
                for record in record_ids:
                    record.unlink()

            for i in range(len(res)):
                if i < 9:
                    detail_id = '0'+str(i+1)
                else:
                    detail_id = str(i+1)
                if res[i][2] == '1':
                    col_type = '1'
                else:
                    col_type = '0'

                detail_obj.create({
                    'pivot_id': self.id,
                    'detail_id': detail_id,
                    'col_order': res[i][0],
                    'col_name': res[i][1],
                    'col_type': col_type,
                    'access_coord': res[i][0],
                })


class statement_pivot_details(models.Model):
    _name = "ps.statement.pivot.details"
    _description = "数据透视定义"

    pivot_id = fields.Many2one('ps.statement.pivot', string='透视编号')
    detail_id = fields.Char(string="明细编号", required=True)
    col_order = fields.Char(string="列坐标", required=True)
    col_name = fields.Char(String="列名称", required=True)
    col_type = fields.Selection([
        ('0', '固定列'),
        ('1', '透视列'),
    ], string="列类型", required=True, default='0')
    access_coord = fields.Char(string="取数坐标", required=True)

    # # col_order = fields.Many2one('ps.statement.sheet.columns', String='列坐标')
    # col_order = fields.Selection(selection='_list_all_columns', string='列坐标', required=True)
    # # col_name = fields.Char(String="列名称", Requird=True)
    # col_name = fields.Selection(selection='_list_all_columnnames', string='列名称', required=True)
    # col_type = fields.Selection([
    #     ('0', '固定列'),
    #     ('1', '透视列'),
    # ], string="列类型", required=True, default='0')
    # # access_coord = fields.Many2one('ps.statement.sheet.columns', String='取数坐标')
    # access_coord = fields.Selection(selection='_list_all_columns', string='取数坐标', required=True)

    # @api.model
    # def _list_all_columns(self):
    #     report_code = self._context.get("report_code")
    #     currentdate = self._context.get("report_date")
    #     if report_code:
    #         query = "SELECT col_order, report_code||'#'||col_name FROM ps_statement_sheet_columns WHERE report_code = '"+report_code+"' AND report_date='"+currentdate+"'"
    #         self._cr.execute(query)
    #         return self._cr.fetchall()
    #
    # @api.model
    # def _list_all_columnnames(self):
    #     report_code = self._context.get("report_code")
    #     currentdate = self._context.get("report_date")
    #     if report_code:
    #         query = "SELECT col_name, report_code||'#'||col_name FROM ps_statement_sheet_columns WHERE report_code = '"+report_code+"' AND report_date='" + currentdate + "'"
    #         self._cr.execute(query)
    #         return self._cr.fetchall()

    # @api.onchange('col_order')
    # def onchange_col_order(self):
    #     currentdate = self.env['ps.statement.statements'].get_fiscalperiod()
    #     query = "SELECT col_order, col_name FROM ps_statement_sheet_columns WHERE report_date='" + currentdate + "'"
    #     self._cr.execute(query)
    #     res = self._cr.fetchall()
    #     if self.col_order:
    #         for line in res:
    #             if line[0] == self.col_order:
    #                 self.col_name = line[1]
    #         self.access_coord = self.col_order

class statement_classify_define(models.Model):
    _name = "ps.statement.classify"
    _description = "报表分类字典"

    code = fields.Char(string="分类编号", required=True)
    name = fields.Char(string="分类名称", required=True)
    classify_details_ids = fields.One2many('ps.statement.classify.details', 'classify_id', string='报表分类')

    @api.model
    def default_get(self, fields):
        classify_ids = self.search([])
        temp = "0"
        for line in classify_ids:
            if int(line.code) > int(temp):
                temp = line.code

        if int(temp) > 8:
            temp = str(int(temp) + 1)
        else:
            temp = "0" + str(int(temp) + 1)
        defaults = super(statement_classify_define, self).default_get(fields)
        defaults['code'] = temp
        return defaults

class statement_classify_details(models.Model):
    _name = "ps.statement.classify.details"
    _description = "报表分类包含报表"

    classify_id = fields.Many2one('ps.statement.classify', string='分类编号')
    report_code = fields.Selection(selection='_list_all_statements', string='报表编号', required=True)
    # report_name = fields.Char(string="报表名称", required=True)

    @api.model
    def _list_all_statements(self):
        currentdate = datetime.today().strftime("%Y-%m-%d")
        period_record_ids = self.env['ps.account.period'].get_period(currentdate)
        if period_record_ids == False:
            fyearperiod = ""
        else:
            if len(period_record_ids) > 1:
                fyearperiod = ""
            else:
                # fyearperiod:该年度的值为当前会计年度，会计区间是当前区间
                fyear = period_record_ids[0].year
                fperiod = period_record_ids[0].period
                fyearperiod = fyear + fperiod

        self._cr.execute(
            "SELECT report_code, report_name FROM ps_statement_statements WHERE report_date = '" + fyearperiod + "'  ORDER BY report_code")
        return self._cr.fetchall()

    # @api.onchange('report_code')
    # def onchange_report_code(self):
    #     currentdate = self.env['ps.statement.statements'].get_fiscalperiod()
    #     query = "SELECT col_order, col_name FROM ps_statement_sheet_columns WHERE report_date='" + currentdate + "'"
    #     self._cr.execute(query)
    #     res = self._cr.fetchall()
    #     if self.col_order:
    #         for line in res:
    #             if line[0] == self.col_order:
    #                 self.col_name = line[1]
    #         self.access_coord = self.col_order

class PsCalculateTemptable(models.Model):
    _name = 'ps.statement.calculate.temptable'
    _description = 'ps.statement.calculate.temptable'
    _auto = False

    #######################################################################
    # 将所有的KMJE或者其他公式的SQL使用UNION拼接形成一个大的视图，完成取数
    #######################################################################
    ye = fields.Float(string='余额')
    formula = fields.Char(string='公式')

    @api.model_cr
    def table_create(self, sql):
        self._table = 'ps_statement_calculate_temptable'
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
            )
        """ % (self._table, sql)
        )



