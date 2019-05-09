# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re

import logging
_logger = logging.getLogger(__name__)


class PsMrpExpenseItem(models.Model):
    _name = "ps.mrp.expense.item"

    code = fields.Char(string='Code')
    name = fields.Char(string='Name', required=True, translate=True)
    cost_item_id = fields.Many2one('ps.mrp.cost.item', string='Cost Item Id')
    company_id = fields.Many2one('res.company', string='Company')

    @api.model
    def create(self, vals):
        # 修改create方法，控制‘code’字段自动生成
        vals['code'] = self.env['ir.sequence'].next_by_code('ps.mrp.expense.item.code')
        return super(PsMrpExpenseItem, self).create(vals)


class PsMrpExpensesStandardSetting(models.Model):
    _name = "ps.mrp.expenses.standard.setting"

    name = fields.Char(string='Program name', required=True)
    cost_type = fields.Selection([('consumablematerial', 'ConsumableMaterial'), ('indirect', 'IndirectExpenses')], string='Cost Type', required=True)
    cost_item = fields.Many2one('ps.mrp.cost.item', string='Cost Item', required=True)
    cost_src_ids = fields.One2many('ps.mrp.expenses.standard.setting.src', 'cost_src_id', string='Cost Sender')
    cost_tar_ids = fields.One2many('ps.mrp.expenses.standard.setting.tar', 'cost_tar_id', string='Cost Receiver')
    company_id = fields.Many2one('res.company', string='Company')
    allocation_standard = fields.Many2one('ps.mrp.expenses.standard', domain=[('standard_type', '=', 'expensesstandard')], string='Allocation Standard' , required=True)

    _sql_constraints = [('check_name_unique', 'unique(name)', 'Program name must be unique!')]

    @api.onchange('allocation_standard')
    def onchange_allocation_standard(self):
        """
            添加onchange依据字段‘allocation_standard’的变化，动态修改前端‘product’字段的数值是否显示
            ·   本方法只适用于修改‘allocation_standard’字段时，才会改变product字段的数值显示
            ·   优先修改本字段再添加‘cost_src_ids’和‘cost_tar_ids’字段时，‘product’字段数值不会发生变化
            ·   需要通过另外一个onchange('cost_tar_ids')来控制
        """
        if self.allocation_standard.scope_application == 'costcenter' or self.allocation_standard.scope_application == False:
            for res in self.cost_tar_ids:
                res.center_product = False
        if self.allocation_standard.scope_application == 'product':
            for res in self.cost_tar_ids:
                res.center_product = True


    @api.onchange('cost_tar_ids')
    def onchange_cost_tar_ids(self):
        self.onchange_allocation_standard()


    @api.onchange('cost_type')
    def onchange_cost_type(self):
        # 添加动态domain，用于过滤cost_type字段，以获取cost_item的值
        if self.cost_type == 'consumablematerial':
            domain = [('cost_type', '=', 'consumable')]
        if self.cost_type == 'indirect':
            domain = [('cost_type', '=', 'indirect')]
        if self.cost_type == False:
            domain = [('cost_type', '=', '')]
        return {
            'domain': {'cost_item': domain}
        }


    @api.model
    def create(self, vals):
        # 修改create方法，控制one2many字段不能为空
        if 'cost_src_ids' not in vals.keys():
            raise ValidationError(_('Please maintain the sender data!'))
        if 'cost_tar_ids' not in vals.keys():
            raise ValidationError(_('Please maintain the receiver data!'))
        return super(PsMrpExpensesStandardSetting, self).create(vals)


    @api.constrains('cost_src_ids', 'cost_tar_ids')
    def _check_src_tar_ids(self):
        # 通过constrains约束，约束one2many字段在编辑时不能为空
        for r in self:
            if not r.cost_src_ids:
                raise ValidationError(_('Please maintain the sender data!'))
            if not r.cost_tar_ids:
                raise ValidationError(_('Please maintain the receiver data!'))


class PsMrpExpensesStandardSettingSrc(models.Model):
    _name = "ps.mrp.expenses.standard.setting.src"

    name = fields.Many2one('ps.mrp.cost.accounting', string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    cost_src_id = fields.Many2one('ps.mrp.expenses.standard.setting', String='Cost Src')


class PsMrpExpensesStandardSettingTar(models.Model):
    _name = "ps.mrp.expenses.standard.setting.tar"

    name_id = fields.Many2one('ps.mrp.cost.accounting', string='Name', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    cost_tar_id = fields.Many2one('ps.mrp.expenses.standard.setting', String='Cost Tar')
    center_product = fields.Boolean(String='center_product', default=True)


class PsMrpExpensesStandard(models.Model):
    _name = "ps.mrp.expenses.standard"

    code = fields.Char(copy=False, string='Code')
    name = fields.Char(string='Name', required=True)
    formula_code = fields.Char(string='Formula Code', required=True)
    scope_application = fields.Selection([('costcenter', 'CostCenter'), ('product', 'product')], string='Scope Application', required=True)
    standard_type = fields.Selection([('expensesstandard', 'expensesStandard'), ('wipstandard', 'WIPStandard')], string='Standard Type', required=True)
    is_factor = fields.Boolean(string='Is Factor')
    factor_ids = fields.Many2many('ps.mrp.expenses.standard.line', docmain=[('is_factor','=',True)], string='Factors')
    compute_formula = fields.Text(string='Compute Formula')
    company_id = fields.Many2one('res.company', string='Company')
    preset_sql = fields.Char(string='Preset Sql')
    preset_parameter = fields.Char(string='Preset Parameter')
    is_preset = fields.Boolean(default=False, string='Is Preset')

    _sql_constraints = [
        ('formula_code_unique', 'UNIQUE(formula_code)', 'Formula Code must be unique!'),
    ]

    @api.multi
    def write(self, vals):

        if self.is_preset:
            # 判断如果是预置数据，则不允许修改
            raise ValidationError(_('Preset data is not allowed to be modified!'))

        # 组织vals数据
        values = {
            'compute_formula': self.vals_settings(vals, 'compute_formula', self.compute_formula),
            'standard_type': self.vals_settings(vals, 'standard_type', self.standard_type),
            'scope_application': self.vals_settings(vals, 'scope_application', self.scope_application),
            'formula_code': self.vals_settings(vals, 'formula_code', self.formula_code),
            'is_factor': self.vals_settings(vals, 'is_factor', self.is_factor),
            'factor_ids': self.vals_settings(vals, 'factor_ids', self.factor_ids),
            'name': self.vals_settings(vals, 'name', self.name),
        }

        if values['compute_formula']:
            # 去除公式因子框中空格引起的错误
            if values['compute_formula'].replace(' ', '') == "":
                values['compute_formula'] = ""
            else:
                values['compute_formula'] = values['compute_formula'].replace(' ', '')
                self.checkout_factor(values, flag='Write')

        if vals['is_factor']:
            # 针对is_factor字段有无进行相应附表的操作
            if not self.env['ps.mrp.expenses.standard.line'].search([('name', '=', values['name'])]):
                self.env['ps.mrp.expenses.standard.line'].create({
                    'name': values['name'],
                    'formula_code': values['formula_code'],
                })
        else:
            del_line = self.env['ps.mrp.expenses.standard.line'].search([('name', '=', self.name)])
            del_line.unlink()

        res = super(PsMrpExpensesStandard, self).write(values)
        return res


    @api.multi
    def unlink(self):
        # 进行附表对应主表删除相应信息

        for r in self:
            # 进行循环获取self，防止同时删除多条数据时，提示报错
            if r.is_preset:
                # 判断如果是预置数据，则不允许删除
                raise ValidationError(_('Preset data is not allowed to be deleted!'))

        for res in self:
            del_line = self.env['ps.mrp.expenses.standard.line'].search([('name', '=', res.name)])
            del_line.unlink()
        return super(PsMrpExpensesStandard, self).unlink()


    @api.model
    def create(self, vals):
        """
            修改create方法：
            ·   控制‘code’字段自动生成
            ·   新建附表，用于辅助公式因子字段判断使用
        """
        if vals['is_preset']:
            # 进行数据预置处理
            vals['code'] = self.env['ir.sequence'].next_by_code('ps.mrp.expenses.standard.code')
            return super(PsMrpExpensesStandard, self).create(vals)

        vals['code'] = self.env['ir.sequence'].next_by_code('ps.mrp.expenses.standard.code')

        if vals['compute_formula']:
            # 去除公式因子框中空格引起的错误
            if vals['compute_formula'].replace(' ', '') == "":
                vals['compute_formula'] = ""
            else:
                vals['compute_formula'] = vals['compute_formula'].replace(' ', '')
                self.checkout_factor(vals, flag='Create')

        if vals['is_factor']:
            # 新建附表数据,用于显示公式因子
            self.env['ps.mrp.expenses.standard.line'].create({
                'name': vals['name'],
                'formula_code': vals['formula_code'],
            })
        return super(PsMrpExpensesStandard, self).create(vals)


    def checkout_factor(self, vals, flag):
        res_list = []
        formula_code_list = re.split("[\+\-\*\/]", vals['compute_formula'].replace(' ', '')) # 定义正则,用于匹配计算符号

        if not self.re_0(formula_code_list, vals):
            # 正则匹配/0的多种情况
            raise ValidationError(_('The formula cannot contain the case of dividing by 0.'))

        # 取many2many字段进行因子判断
        if flag == 'Create':
            # 如果是create, 则直接通过vals传入的值进行操作
            for res in self.env['ps.mrp.expenses.standard.line'].search([('id', 'in', vals['factor_ids'][0][2])]):
                res_list.append(res.formula_code)

        if flag == 'Write':
            # 如果是write,则通过self进行获取值再操作
            list_id = []
            for id in self.factor_ids:
                list_id.append(id.id)
            for res in self.env['ps.mrp.expenses.standard.line'].search([('id', 'in', list_id)]):
                res_list.append(res.formula_code)

        # 获取当前formula_code字段输入框中的内容,并进行拆分
        for formula_code in formula_code_list:
            if formula_code not in res_list:
                if not self.is_number(formula_code):
                    raise ValidationError(formula_code + _(' Incorrect filling in formula factor.'))


    def re_0(self, formula_code_list, vals):
        # 正则匹配/0的多种情况
        re_match_0 = r"\/0+.?0*[\+\-\*\/]"  # 定义正则1,匹配中间/0或/0.0的情况
        res_match_0 = re.findall(re_match_0, vals['compute_formula'].replace(' ', ''))
        if res_match_0:
            return False
        else:
            if self.is_number(formula_code_list[len(formula_code_list) - 1]):
                The_last_symbol = vals['compute_formula'].replace(' ', '')[len(vals['compute_formula'].replace(' ', ''))-len(formula_code_list[len(formula_code_list) - 1])-1:len(vals['compute_formula'].replace(' ', ''))-len(formula_code_list[len(formula_code_list) - 1]):] # 取最后一个符号,判断是否为/
                if The_last_symbol == '/':
                    re_match_0 = r"^(0+.?0*)$"  # 定义正则2,匹配结尾/0或/0.0的情况
                    res_match_0 = re.findall(re_match_0, formula_code_list[len(formula_code_list) - 1])
                    if res_match_0:
                        return False
        return True


    def is_number(self, num):
        # 判断取数为数字(int/float)
        pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
        result = pattern.match(num)
        if result:
            if num == result.group(0):
                return True
            else:
                return False
        else:
            return False


    def vals_settings(self, vals, key, self_key):
        # 解决因未修改,而未通过write方法传入vals值的问题,传入则使用vals,否则使用self
        if vals.get(key, 'NNN') == 'NNN':
            vals[key] = self_key
        return vals[key]


class PsMrpExpensesStandardLine(models.Model):
    _name = "ps.mrp.expenses.standard.line"

    name = fields.Char(string='Name')
    formula_code = fields.Char(string='Formula Code')