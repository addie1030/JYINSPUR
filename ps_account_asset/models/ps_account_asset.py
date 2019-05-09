# -*- coding: utf-8 -*-

import time
import math
from odoo.fields import Date
from datetime import date, datetime
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools
from odoo.tools import float_compare, float_is_zero
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta


class PsAccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    # 修正remaining_value有时为-0的情况
    @api.multi
    def create_move(self, post_move=True):
        res = super(PsAccountAssetDepreciationLine, self).create_move(post_move)
        for line in self:
            line.remaining_value = abs(line.remaining_value)
            analytic_lines = []
            if line.asset_id.ps_department_ids:
                sum_line_amount = 0
                for index,department in enumerate(line.asset_id.ps_department_ids):
                    if index < len(line.asset_id.ps_department_ids)-1:
                        line_amount =  round(department.ps_proportional * line.amount / 100,precision_digits=2)
                        sum_line_amount = sum_line_amount + line_amount
                    else:
                        line_amount = round(line.amount - sum_line_amount,precision_digits=2)
                    analytic_line = {
                        'account_id': department.ps_analytic_id.id,
                        'name': department.ps_analytic_id.name,
                        'amount': line_amount,
                    }
                    new_line = self.env['account.analytic.line'].create(analytic_line)
                    analytic_lines.append(new_line)
                for move_line in line.move_id.line_ids:
                    if move_line.debit != 0:
                        pamls_vals = {
                            'amount_input': move_line.debit,
                            'analytic_line_ids': [(4,x.id) for x in analytic_lines],
                        }
                        ps_sub = self.env['ps.account.move.line.sub'].create(pamls_vals)
                        move_line.update({
                            'analytic_line_ids': [x.id for x in analytic_lines],
                            'ps_sub_id': ps_sub.id,
                        })
                        break
        return res

class PsAccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'


    ps_depreciation_amount = fields.Float(digits=(16, 2),compute='_amount_residual', string='Total Depreciation') #累计折旧
    ps_change_mode_id = fields.Many2one('ps.asset.change.mode', string='Asset Change Mode', required=True) #资产来源
    ps_asset_state_id = fields.Many2one('ps.asset.state', string='Asset State', required=True) #资产状态
    ps_location_id = fields.Many2one('ps.asset.location', string='Location') #资产位置
    ps_plan_months = fields.Integer(string='Total Plan Months') #累计使用月数
    ps_accrued_months = fields.Integer(string='Accrued Months', compute='_compute_ps_accrued_months') #已计提月数
    ps_asset_uom_id = fields.Many2one('uom.uom', string='UOM') #计量单位
    ps_monthly_amount = fields.Float(digits=(16, 2), string="Month Depreciation Value", compute='_compute_ps_monthly_amount') #月折旧额
    ps_asset_quantity = fields.Integer(string="Asset Quantity", default=1) #数量
    ps_asset_barcode = fields.Char(string='Barcode', requird=False) #条码
    ps_is_initial= fields.Boolean(string='Initial',default=False) #期初标志
    move_id = fields.Many2one('account.move', string=' Account Move', copy=False) #增加凭证ID
    ps_change_mode_category = fields.Selection(string='Change Mode Category', related='ps_change_mode_id.category') #资产来源类别
    ps_department_ids = fields.One2many('ps.asset.department', 'ps_asset_id', string='Department') #部门
    ps_init_amount = fields.Float(digits=(16, 2), string="Initial Total Depreciation" ) # 期初累计
    salvage_value = fields.Float(string='Salvage Value', digits=0,
                                 compute='_compute_salvage_value',
                                 states={'draft': [('readonly', False)]},
                                 help="It is the amount you plan to have that you cannot depreciate.") #净残值
    create_card_date = fields.Date(string='Create Card Date', required=True, readonly=True,
                                         states={'draft': [('readonly', False)]}, default=fields.Date.context_today) #建卡日期

    ps_is_depreciation = fields.Boolean(string='Depreciation', related='ps_asset_state_id.is_depreciation')  # 是否计提折旧
    ps_alteration_line_ids = fields.One2many('ps.asset.alteration.line', 'asset_id', string='Alteration Lines')     #变动明细
    ps_disposal_line_ids = fields.One2many('ps.asset.disposal.line', 'asset_id', string='Disposal Lines')   #处置明细
    ps_is_disposal = fields.Boolean(string='Disposal State', default=False)  # 处置状态

    _sql_constraints = [('code_unique', 'UNIQUE(code)', "The code must be unique!"),
                        ('name_unique', 'UNIQUE(name)', "The name must be unique!")]

    # 计算净残值
    @api.one
    @api.depends('category_id', 'value')
    def _compute_salvage_value(self):
        if self.category_id:
            self.salvage_value = self.value * self.category_id.ps_net_salvage_rate / 100

    # 次月生成折旧版
    @api.model
    def create(self, vals):
        if not vals.get('ps_change_mode_id'):
            vals.update({'ps_change_mode_id': self.env['ps.asset.change.mode'].search([('is_default','=','True'),('category','=','add'),('active','=','True')])[0].id})

        record = self.env['account.asset.category'].search(
                [('id', '=', int(vals['category_id']))])

        if not vals.get('ps_asset_state_id'):
            if record.ps_asset_state_id:
                vals.update({'ps_asset_state_id': record.ps_asset_state_id.id})
            else:
                vals.update({'ps_asset_state_id': self.env['ps.asset.state'].search([('active', '=', 'True')])[0].id})

        if not vals.get('ps_asset_uom_id'):
            if record.ps_asset_uom_id:
                vals.update({'ps_asset_uom_id': record.ps_asset_uom_id.id})

        init_total = vals.get('ps_init_amount')
        if init_total != 0:
            compute_date = fields.Date.to_string(datetime.now() + relativedelta(months=1))
            vals['date'] = compute_date
            res = super(PsAccountAssetAsset, self).create(vals)
        else:
            res = super(PsAccountAssetAsset, self).create(vals)
        depreciation_lines = self.env['account.asset.depreciation.line'].search([('asset_id', '=', res.id)])
        for line in depreciation_lines:
            line.remaining_value = abs(line.remaining_value) #净残值为0时修正最后一行残留为-0的情况
        return res

    # 折旧累计金额及净值计算调整
    @api.one
    @api.depends('value', 'salvage_value', 'depreciation_line_ids.move_check', 'depreciation_line_ids.amount','ps_init_amount')
    def _amount_residual(self):
        total_amount = 0.0
        for line in self.depreciation_line_ids:
            if line.move_check:
                total_amount += line.amount
        self.value_residual = self.value - total_amount - self.salvage_value - self.ps_init_amount
        self.ps_depreciation_amount = self.value - self.value_residual - self.salvage_value

    @api.depends('depreciation_line_ids')
    def _compute_ps_monthly_amount(self):
        """
        计算下次折旧额:
        1.当月未折旧,选取当月折旧额
        2.当月已折旧,选取下一月折旧额
        3.最后一个月折旧之后显示为0
        """
        date_list = []
        if self.depreciation_line_ids:
            for line in self.depreciation_line_ids:
                date_list.append(line.depreciation_date.strftime(DF)[:7])
            for line in self.depreciation_line_ids:
                if Date.today().strftime(DF)[:7] < min(date_list)[:7]:
                    self.ps_monthly_amount = line.amount
                    break
                elif Date.today().strftime(DF)[:7] > max(date_list)[:7]:
                    self.ps_monthly_amount = 0.0
                    break
                elif Date.today().strftime(DF)[:7] == line.depreciation_date.strftime(DF)[:7]:
                    if not line.move_check:
                        self.ps_monthly_amount = line.amount
                        break
                    else:
                        if self.method == 'degressive':
                            self.ps_monthly_amount = line.remaining_value * self.category_id.method_progress_factor
                            break
                        elif self.method == 'linear' and line.remaining_value != 0:
                            self.ps_monthly_amount = line.amount
                            break
                        elif self.method == 'linear' and line.remaining_value == 0:
                            self.ps_monthly_amount = 0.0
                            break
                        else:
                            # TODO 以后新增的折旧方法
                            self.ps_monthly_amount = 0.0
                            break
                else:
                    pass
        return

    # 计算已计提折旧月数
    def _compute_ps_accrued_months(self):
        if self.depreciation_line_ids:
            domain = [('asset_id','=',self.id),('move_check','=',True)]
            depreciation_lines = self.env['account.asset.depreciation.line'].search(domain)
            self.ps_accrued_months = len(depreciation_lines)

    # 选择资产类别带出资产类别里的状态
    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.category_id:
            self.ps_asset_state_id = self.category_id.ps_asset_state_id.id
            self.ps_asset_uom_id = self.category_id.ps_asset_uom_id.id

    # 部门页签下的分配比例只能为100%
    @api.constrains('ps_department_ids')
    def _check_ps_department_ids(self):
        if self.ps_department_ids: # 点击创建按钮时不校验
            if sum([dep.ps_proportional for dep in self.ps_department_ids]) != 100:
                raise ValidationError(_('Distribution proportional sum must be 100!'))

    # 生成凭证
    @api.multi
    def generate_account_move(self):
        if self.ps_change_mode_id:
            if not self.ps_change_mode_id.account_change_id:
                raise UserError(_('Please configure Asset Account in Asset Change Mode'))
            if not self.ps_change_mode_id.journal_id:
                raise UserError(_('Please configure Journal in Asset Change Mode'))
        if self.ps_is_initial:
            raise UserError(_('The initial mark is set, can not generate account move!'))
        if self.move_id:
            raise UserError(_('This asset card is already linked to a journal entry! Please post or delete it.'))
        account_period= self.env['ps.account.period'].search([('date_start','<',self.date),('date_end','>',self.date)])
        for period in account_period:
            if period.financial_state==2:
                raise UserError(_('Date out of account period, can not generate account move!'))
        self.ensure_one()
        change_mode = self.ps_change_mode_id
        if change_mode.category == 'add':
            debit_account_id = self.category_id.account_asset_id.id
            credit_account_id = change_mode.account_change_id.id
        depreciation_account_id = self.category_id.account_depreciation_id.id
        depreciation_date = self.env.context.get('date') or fields.Date.context_today(self)
        company_currency = self.company_id.currency_id
        current_currency = self.currency_id
        debit_amount = current_currency.with_context(date=depreciation_date).compute(self.value, company_currency)
        credit_amount_depreciation = current_currency.with_context(date=depreciation_date).compute(self.ps_depreciation_amount, company_currency)
        credit_amount_residual = current_currency.with_context(date=depreciation_date).compute((self.value-self.ps_depreciation_amount), company_currency)
        asset_name = self.name
        move_line_debit = {
            'name': asset_name,
            'account_id': debit_account_id,
            'credit': 0.0,
            'debit': debit_amount,
            'journal_id': change_mode.journal_id.id,
            'partner_id': self.partner_id.id,
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and debit_amount or 0.0,
        }
        move_line_credit_depreciation = {
            'name': asset_name,
            'account_id': depreciation_account_id,
            'debit': 0.0,
            'credit': credit_amount_depreciation,
            'journal_id': change_mode.journal_id.id,
            'partner_id': self.partner_id.id if self.partner_id else None,
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * credit_amount_depreciation or 0.0,
        }
        move_line_credit_residual = {
            'name': asset_name,
            'account_id': credit_account_id,
            'debit': 0.0,
            'credit': credit_amount_residual,
            'journal_id': change_mode.journal_id.id,
            'partner_id': self.partner_id.id if self.partner_id else None,
            'analytic_account_id': False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * credit_amount_residual or 0.0,
        }
        line_ids = []
        if self.ps_depreciation_amount != 0:
            line_ids = [(0, 0, move_line_debit),(0, 0, move_line_credit_depreciation),(0, 0, move_line_credit_residual)]
        else:
            line_ids = [(0, 0, move_line_debit),(0, 0, move_line_credit_residual)]

        move_vals = {
            'ref': self.code,
            'date': self.create_date or False,
            'journal_id': self.ps_change_mode_id.journal_id.id,
            'line_ids': line_ids,
        }

        move = self.env['account.move'].create(move_vals)
        self.write({
            'move_id': move.id
        })
        domain = [('res_model', '=', 'account.move'), ('res_id', '=', move.id)]
        account_move_view = self.env.ref('account.view_move_form')
        return {
            'name': move.name,
            'domain': domain,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_id': account_move_view.id,
            'views': [(account_move_view.id, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'res_id': move.id,
        }


    @api.multi
    def compute_depreciation_board(self):
        if self.ps_is_depreciation:
            res = super(PsAccountAssetAsset, self).compute_depreciation_board()
            if self.depreciation_line_ids:
                for depreciation_line in self.depreciation_line_ids:
                    depreciation_line.remaining_value = abs(depreciation_line.remaining_value)
            return res
