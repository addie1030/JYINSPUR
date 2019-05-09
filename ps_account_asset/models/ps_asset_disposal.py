# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.float_utils import float_round as round

class PsAssetAssetDisposal(models.Model):
    _name = 'ps.asset.disposal'
    _description = 'Asset Disposal'


    name = fields.Char(string='Name', requird=True,copy=False,
                       default=lambda self: _('New')) #资产处置名称
    date = fields.Date(string='Date', required=True, states={'draft': [('readonly', False)]}, default=fields.Date.context_today) #单据日期
    disposal_date = fields.Date(string='Disposal Date', required=True, states={'draft': [('readonly', False)]}, default=fields.Date.context_today) #处置日期
    change_id = fields.Many2one('ps.asset.change.mode', string='Income Disposal Mode', required=True)  # 资产来源
    change_expense_id = fields.Many2one('ps.asset.change.mode', string='Expense Disposal Mode', required=True)  # 清理费用
    user_id = fields.Many2one('res.users', string='Disposal Person',default=lambda self: self.env.user)  # 处置人
    company_id = fields.Many2one('res.company', string='Company') #公司
    state = fields.Selection([('draft', 'Draft'), ('checked', 'Confirmed'), ('done', 'Done')], string='Status',
                             required=True, readonly=True, copy=False, default='draft') # 状态
    cause = fields.Char(string='Disposal Cause')  # 处置原因
    disposal_line_ids = fields.One2many('ps.asset.disposal.line', 'disposal_id', string='Disposal Detail')  # 处置明细行
    account_move_is_created = fields.Boolean(string='Depreciation', defalt=False)  # 折旧状态

    @api.model
    def create(self, vals):
        """
        按规则生成单据号
        :param vals:
        :return: name
        """
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ps.asset.disposal') or _('New')
        if not vals.get('disposal_line_ids'):
            raise UserError(_('Disposal line must be required!'))
        return super(PsAssetAssetDisposal, self).create(vals)

    @api.constrains('disposal_line_ids')
    def _check_disposal_line_ids(self):
        for line in self:
            if not line.disposal_line_ids:
                raise UserError(_('Disposal line must be required!'))

    @api.multi
    def unlink(self):
        for disposal in self:
            if disposal.state != 'draft':
                raise ValidationError(_('Asset Disposal ') + disposal.name + _(' state is not draft, can not delete.'))
        return super(PsAssetAssetDisposal, self).unlink()

    @api.multi
    def validate(self):
        """
        确认单据
        """
        for line in self.disposal_line_ids:
            if line.asset_id.ps_is_disposal:
                raise ValidationError(_('Asset ') + line.asset_id.name + _(' has already disposal!'))
                break
        else:
            for line in self.disposal_line_ids:
                line.asset_id.ps_is_disposal = True
            self.write({'state': 'checked'})

    def generate_account_moves(self):
        """
        生成凭证
        """
        if self.account_move_is_created:
            raise UserError(_('This disposal has already generated account moves!'))
        if self.disposal_line_ids:
            for line in self.disposal_line_ids:
                line.create_moves()
        self.write({'state': 'done'})

class PsAssetAssetDisposalLine(models.Model):
    _name = 'ps.asset.disposal.line'
    _description = 'Asset Disposal Line'

    disposal_id = fields.Many2one('ps.asset.disposal', string='Disposal',ondelete="cascade", required=True)  # 处置单
    asset_id = fields.Many2one('account.asset.asset', string='Asset', required=True)  # 资产
    code = fields.Char(string='Asset Code',related='asset_id.code', readonly=True)  # 资产编号
    asset_uom_id = fields.Many2one('uom.uom', string='Asset Uom', related='asset_id.ps_asset_uom_id', readonly=True)  # 计量单位
    asset_qty = fields.Integer(string='Asset Quantity', related='asset_id.ps_asset_quantity', readonly=True)  # 数量
    value = fields.Float(digits=(16, 2), string="Asset Value", related='asset_id.value', readonly=True)  # 原值
    depreciation_all = fields.Float(digits=(16, 2), string="Accumulated Depreciation",
                                     related='asset_id.ps_depreciation_amount', readonly=True)  # 累计折旧
    depreciation_month = fields.Float(digits=(16, 2), string="Depreciation this month", readonly=False)  # 本月折旧
    income = fields.Float(digits=(16, 2), string="Clearing Income")  # 清理收入
    expense = fields.Float(digits=(16, 2), string="Clearing expense")  # 清理费用
    abstract = fields.Char(string='Abstract')  # 摘要
    is_voucher = fields.Boolean(string='Is Generation Voucher', default=False)  # 是否已生成凭证
    depreciation_move_id = fields.Many2one('account.move', string='Depreciation Voucher', copy=False)  # 累计折旧凭证
    income_move_id = fields.Many2one('account.move', string='Clearing Income Voucher', copy=False)  # 清理收入凭证
    expense_move_id = fields.Many2one('account.move', string='Clearing Expense Voucher', copy=False)  # 清理费用凭证
    disposal_move_id = fields.Many2one('account.move', string='Asset Disposal Voucher', copy=False)  # 资产清理凭证
    value_residual = fields.Float(digits=(16, 2), string=" Net asset value", related='asset_id.value_residual', readonly=True)  # 资产净值
    depreciation_is_done = fields.Boolean(string='Depreciation', defalt=False)  # 折旧状态
    depreciation_state_is_depreciation = fields.Boolean(string='Depreciation', related='asset_id.ps_asset_state_id.is_depreciation', defalt=False)  # 是否可折旧

    @api.constrains('income','expense')
    def _check_income_expense(self):
        """
        保存时清理费用+清理收入不能等于0
        """
        for line in self:
            if line.income>=0 and line.expense>=0:
                if sum([line.income,line.expense]) == 0:
                    raise ValidationError(_('at least one Income and Expense is greater than 0!'))

    @api.constrains('depreciation_month')
    def _check_depreciation_month(self):
        """
        本月折旧大于等于0且小于等于剩余计提
        剩余计提 = 原值-累计折旧-净残值 (从资产卡片取值)
        residual = value - ps_depreciation_amount - salvage_value
        """
        for line in self:
            residual = line.asset_id.value - line.asset_id.ps_depreciation_amount - line.asset_id.salvage_value
            if line.depreciation_month < 0:
                raise ValidationError(_('Depreciation month should be greater than or equal to 0!'))
            if line.depreciation_month > residual:
                raise ValidationError(_('Depreciation month should be less than or equal to residual value:%s'%(residual)))

    @api.constrains('abstract')
    def _check_abstract(self):
        for line in self:
            if not line.abstract:
                raise ValidationError(_('Abstract must be required!'))

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        """
        选择资产时判断当月是否已计提折旧,更新折旧状态用于月折旧额的只读条件判断
        """
        if self.asset_id.depreciation_line_ids:
            for line in self.asset_id.depreciation_line_ids:
                if self.disposal_id.disposal_date.strftime(DF)[:7] == line.depreciation_date.strftime(DF)[:7]:
                    if line.move_check:
                        self.depreciation_is_done = True
                        self.depreciation_month = 0.0
                    else:
                        self.depreciation_month = line.amount
                    break

    def create_moves(self):
        self.asset_move()
        if self.depreciation_month != 0:
            self.depreciation_move()
        else:
            pass
        if self.income != 0:
            self.income_move()
        else:
            pass
        if self.expense != 0:
            self.expense_move()
        else:
            pass

    def depreciation_move(self):
        """
        折旧生成的凭证
        """
        journal_id = self.asset_id.category_id.journal_id.id,
        date = self.disposal_id.date or fields.Date.context_today(self)
        company_currency = self.asset_id.company_id.currency_id
        current_currency = self.asset_id.currency_id
        amount = current_currency.with_context(date=date).compute(self.depreciation_month, company_currency)
        asset_name = self.asset_id.name
        analytic_lines = []
        if self.asset_id.ps_department_ids:
            sum_line_amount = 0
            for index,department in enumerate(self.asset_id.ps_department_ids):
                if index < len(self.asset_id.ps_department_ids) - 1:
                    line_amount = round(department.ps_proportional * self.depreciation_month / 100, precision_digits=2)
                    sum_line_amount = sum_line_amount + line_amount
                else:
                    line_amount = round(self.depreciation_month - sum_line_amount, precision_digits=2)
                analytic_line = {
                    'account_id': department.ps_analytic_id.id,
                    'name': department.ps_analytic_id.name,
                    'amount': line_amount,
                }
                new_line = self.env['account.analytic.line'].create(analytic_line)
                analytic_lines.append(new_line)
            pamls_vals = {
                'amount_input': self.depreciation_month,
                'analytic_line_ids': [(4, x.id) for x in analytic_lines],
            }
            ps_sub = self.env['ps.account.move.line.sub'].create(pamls_vals)
        move_line_debit = {
            'name': asset_name,
            'account_id': self.asset_id.category_id.account_depreciation_expense_id.id,
            'credit': 0.0,
            'debit': amount,
            'journal_id': journal_id,
            'ps_sub_id': ps_sub.id if self.asset_id.ps_department_ids else False,
            'analytic_line_ids': [(4,x.id) for x in analytic_lines],
            # FIXME analytic_account_id 做完卡片部门信息之后修正
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and amount or 0.0,
        }
        move_line_credit = {
            'name': asset_name,
            'account_id': self.asset_id.category_id.account_depreciation_id.id,
            'debit': 0.0,
            'credit': amount,
            'journal_id': journal_id,
            # FIXME analytic_account_id 做完卡片部门信息之后修正
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * amount or 0.0,
        }
        move_vals = {
            'ref': self.asset_id.code,
            'date': self.disposal_id.date or False,
            'journal_id': journal_id,
            'line_ids': [(0, 0, move_line_debit), (0, 0, move_line_credit)],
        }
        move = self.env['account.move'].create(move_vals)
        self.disposal_id.account_move_is_created = True
        self.write({
            'is_voucher': True,
            'depreciation_move_id': move.id
        })
        unlink_flag = False
        for depreciation_line in self.asset_id.depreciation_line_ids:
            if unlink_flag:
                depreciation_line.unlink()
            else:
                if self.disposal_id.disposal_date.strftime(DF)[:7] == depreciation_line.depreciation_date.strftime(DF)[:7] and not depreciation_line.move_check:
                    if self.depreciation_month != 0:
                        deviation = self.depreciation_month - depreciation_line.amount
                        depreciation_line.amount = self.depreciation_month
                        depreciation_line.depreciated_value = depreciation_line.depreciated_value + deviation
                        depreciation_line.remaining_value = depreciation_line.remaining_value - deviation
                        depreciation_line.create_move(post_move=True)
                        unlink_flag = True
        self.asset_id.state = 'close'

    def income_move(self):
        """
        收入生成凭证
        """
        journal_id = self.disposal_id.change_id.journal_id.id,
        date = self.disposal_id.date or fields.Date.context_today(self)
        company_currency = self.asset_id.company_id.currency_id
        current_currency = self.asset_id.currency_id
        amount = current_currency.with_context(date=date).compute(self.income, company_currency)
        asset_name = self.asset_id.name
        move_line_debit = {
            'name': asset_name,
            'account_id': self.disposal_id.change_id.account_change_id.id,
            'credit': 0.0,
            'debit': amount,
            'journal_id': journal_id,
            # FIXME analytic_account_id 做完卡片部门信息之后修正
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and amount or 0.0,
        }
        move_line_credit = {
            'name': asset_name,
            'account_id': self.asset_id.category_id.ps_account_asset_disposal_id.id,
            'debit': 0.0,
            'credit': amount,
            'journal_id': journal_id,
            # FIXME analytic_account_id 做完卡片部门信息之后修正
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * amount or 0.0,
        }
        move_vals = {
            'ref': self.asset_id.code,
            'date': self.disposal_id.date or False,
            'journal_id': journal_id,
            'line_ids': [(0, 0, move_line_debit), (0, 0, move_line_credit)],
        }
        move = self.env['account.move'].create(move_vals)
        self.disposal_id.account_move_is_created = True
        self.write({
            'is_voucher': True,
            'income_move_id': move.id
        })
        self.asset_id.state = 'close'

    def expense_move(self):
        """
        费用生成凭证
        """
        journal_id = self.disposal_id.change_expense_id.journal_id.id,
        date = self.disposal_id.date or fields.Date.context_today(self)
        company_currency = self.asset_id.company_id.currency_id
        current_currency = self.asset_id.currency_id
        amount = current_currency.with_context(date=date).compute(self.expense, company_currency)
        asset_name = self.asset_id.name
        move_line_debit = {
            'name': asset_name,
            'account_id': self.asset_id.category_id.ps_account_asset_disposal_id.id,
            'credit': 0.0,
            'debit': amount,
            'journal_id': journal_id,
            # FIXME analytic_account_id 做完卡片部门分析账户信息之后修正
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and amount or 0.0,
        }
        move_line_credit = {
            'name': asset_name,
            'account_id': self.disposal_id.change_expense_id.account_change_id.id,
            'debit': 0.0,
            'credit': amount,
            'journal_id': journal_id,
            # FIXME analytic_account_id 做完卡片部门信息之后修正
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * amount or 0.0,
        }
        move_vals = {
            'ref': self.asset_id.code,
            'date': self.disposal_id.date or False,
            'journal_id': journal_id,
            'line_ids': [(0, 0, move_line_debit), (0, 0, move_line_credit)],
        }
        move = self.env['account.move'].create(move_vals)
        self.disposal_id.account_move_is_created = True
        self.write({
            'is_voucher': True,
            'expense_move_id': move.id
        })
        self.asset_id.state = 'close'

    def asset_move(self):
        """
        资产净值转入资产清理生成凭证
        """
        journal_id = self.asset_id.category_id.journal_id.id,
        date = self.disposal_id.date or fields.Date.context_today(self)
        company_currency = self.asset_id.company_id.currency_id
        current_currency = self.asset_id.currency_id

        for line in self.asset_id.depreciation_line_ids:
            if self.disposal_id.disposal_date.strftime(DF)[:7] == line.depreciation_date.strftime(DF)[:7] and not line.move_check:
                depre_amt = self.asset_id.ps_depreciation_amount + self.depreciation_month
                break
            else:
                depre_amt = self.asset_id.ps_depreciation_amount
        debit_depreciation_amount = current_currency.with_context(date=date).compute(depre_amt, company_currency)
        debit_disposal_amount_origin = self.asset_id.value - depre_amt  # 处置金额
        debit_disposal_amount = current_currency.with_context(date=date).compute(debit_disposal_amount_origin, company_currency)
        credit_amount = current_currency.with_context(date=date).compute(self.asset_id.value, company_currency)
        asset_name = self.asset_id.name
        move_line_debit_depreciation = {
            'name': asset_name,
            'account_id': self.asset_id.category_id.account_depreciation_id.id,
            'credit': 0.0,
            'debit': debit_depreciation_amount,
            'journal_id': journal_id,
            # FIXME analytic_account_id 做完卡片部门信息之后修正
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and debit_depreciation_amount or 0.0,
        }
        move_line_debit_disposal = {
            'name': asset_name,
            'account_id': self.asset_id.category_id.ps_account_asset_disposal_id.id,
            'credit': 0.0,
            'debit': debit_disposal_amount,
            'journal_id': journal_id,
            # FIXME analytic_account_id 做完卡片部门信息之后修正
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and debit_disposal_amount or 0.0,
        }
        move_line_credit = {
            'name': asset_name,
            'account_id': self.asset_id.category_id.account_asset_id.id,
            'debit': 0.0,
            'credit': credit_amount,
            'journal_id': journal_id,
            # FIXME analytic_account_id 做完卡片部门信息之后修正
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * credit_amount or 0.0,
        }
        move_vals = {
            'ref': self.asset_id.code,
            'date': self.disposal_id.date or False,
            'journal_id': journal_id,
            'line_ids': [(0, 0, move_line_debit_depreciation), (0, 0, move_line_debit_disposal),(0, 0, move_line_credit)],
        }
        move = self.env['account.move'].create(move_vals)
        self.disposal_id.account_move_is_created = True
        self.write({
            'is_voucher': True,
            'disposal_move_id': move.id
        })
        self.asset_id.state = 'close'
