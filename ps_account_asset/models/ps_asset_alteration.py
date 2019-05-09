# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class PsAssetAlteration(models.Model):
    _name = 'ps.asset.alteration'
    _description = 'Asset Alteration'

    name = fields.Char(string='Document No.', default=lambda self: _('New'), requird=True)     #单据编号
    date = fields.Date(string='Document Date', default=fields.Date.context_today, requird=True)     #单据日期
    change_date = fields.Date(string='Change Date', default=fields.Date.context_today, requird=True)     # 变动日期
    change_id = fields.Many2one('ps.asset.change.mode', string='Change Mode')  # 变动方式
    user_id = fields.Many2one('res.users', default=lambda self: self._uid, string='Altered Person')     #变更人
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)   #公司
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('posted', 'Posted')
        ], 'Status', default='draft', required=True)    #状态
    cause = fields.Char(string='Change Cause')     #变更原因
    is_category = fields.Boolean(string='Is Alter Category', default=False)    #是否变更类型
    is_asset_state = fields.Boolean(string='Is Alter Asset State', default=False)    #是否变更状态
    is_location = fields.Boolean(string='Is Alter Location', default=False)    #是否变更位置
    is_quantity = fields.Boolean(string='Is Alter Quantity', default=False)    #是否变更数量
    is_value = fields.Boolean(string='Is Alter Value', default=False)    #是否变更原值
    is_init_total = fields.Boolean(string='Is Alter Init Total', default=False)    #是否变更累计折旧
    is_salvage_value = fields.Boolean(string='Is Alter Salvage Value', default=False)    #是否变更净残值
    is_method_number = fields.Boolean(string='Is Alter Method Number', default=False)    #是否变更预计使用月数
    line_ids = fields.One2many('ps.asset.alteration.line', 'alteration_id', string='Alteration Line') #变更明细

    @api.model
    def create(self, vals):
        if not vals.get('line_ids'):
            raise UserError(
                _('Alteration lines is not exist.Please check.'))

        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ps.asset.alteration') or _('New')

        if vals.get('is_init_total') == True:
            for r in vals.get('line_ids'):
                # 检查当月是否已经计提折旧，已经计提折旧则不允许进行累计折旧变更
                account_period = self.env['ps.account.period'].search(
                    [('date_start', '<', fields.Date.today()), ('date_end', '>', fields.Date.today())])

                if account_period:
                    linedate = ''
                    movecheck = False
                    depreciation_lines = self.env['account.asset.depreciation.line'].search([('asset_id', '=', r[2].get('asset_id'))])
                    for line in depreciation_lines:
                        if line.move_check:
                            linedate = line.depreciation_date
                            movecheck = True

                    if movecheck and linedate >= account_period.date_start and linedate <= account_period.date_end:
                        raise UserError(
                            _('Asset ID ') + str(r[2].get('asset_id')) + _(' depreciation has been made and the accumulated depreciation cannot be changed.'))
                    else:
                        asset = self.env['account.asset.asset'].search(
                            [('id', '=', r[2].get('asset_id'))])
                        asset.write({'ps_depreciation_amount': r[2].get('latter_depreciation')})
                        asset.compute_depreciation_board()
                else:
                    raise UserError(
                        _('Period is not exist.Please check.'))

        return super(PsAssetAlteration, self).create(vals)

    @api.multi
    def write(self, vals):
        if self.env.context.get('action') != 'validate':
            if not vals.get('line_ids') or not vals.get('line_ids')[0][2]:
                raise UserError(
                    _('Alteration lines is not exist.Please check.'))

        if vals.get('is_init_total') == True:
            for r in vals.get('line_ids'):
                # 检查当月是否已经计提折旧，已经计提折旧则不允许进行累计折旧变更
                account_period = self.env['ps.account.period'].search(
                    [('date_start', '<', fields.Date.today()), ('date_end', '>', fields.Date.today())])

                if account_period:
                    linedate = ''
                    movecheck = False
                    depreciation_lines = self.env['account.asset.depreciation.line'].search([('asset_id', '=', r[2].get('asset_id'))])
                    for line in depreciation_lines:
                        if line.move_check:
                            linedate = line.depreciation_date
                            movecheck = True

                    if movecheck and linedate >= account_period.date_start and linedate <= account_period.date_end:
                        raise UserError(
                            _('Asset ID ') + str(r[2].get('asset_id')) + _(' depreciation has been made and the accumulated depreciation cannot be changed.'))
                    else:
                        asset = self.env['account.asset.asset'].search(
                            [('id', '=', r[2].get('asset_id'))])
                        asset.write({'ps_depreciation_amount': r[2].get('latter_depreciation')})
                        asset.compute_depreciation_board()
                else:
                    raise UserError(
                        _('Period is not exist.Please check.'))

        return super(PsAssetAlteration, self).write(vals)

    @api.multi
    def validate(self):
        self.with_context({'action': 'validate'}).write({'state': 'confirmed'})
        for r in self.line_ids:
            r.former_category_id = r.asset_id.category_id
            r.former_location_id = r.asset_id.ps_location_id
            r.former_asset_state_id = r.asset_id.ps_asset_state_id
            r.former_quantity = r.asset_id.ps_asset_quantity
            r.former_value = r.asset_id.value
            r.former_depreciation = r.asset_id.ps_init_amount
            r.former_salvage_value = r.asset_id.salvage_value
            r.former_method_number = r.asset_id.method_number
            if r.latter_category_id:
                r.asset_id.category_id = r.latter_category_id
            if r.latter_location_id:
                r.asset_id.ps_location_id = r.latter_location_id
            if r.latter_asset_state_id:
                r.asset_id.ps_asset_state_id = r.latter_asset_state_id
            if r.latter_quantity:
                r.asset_id.ps_asset_quantity = r.latter_quantity
            if r.latter_value:
                r.asset_id.value = r.latter_value
            if r.latter_depreciation:
                r.asset_id.ps_init_amount = r.latter_depreciation
            if r.latter_salvage_value:
                r.asset_id.salvage_value = r.latter_salvage_value
            if r.latter_method_number:
                r.asset_id.method_number = r.latter_method_number
            r.asset_id.compute_depreciation_board()
            r.state = 'confirmed'

    @api.multi
    def create_move(self):
        if self.is_value == True:
            for r in self.line_ids:
                if r.move_id and r.is_journal:
                    raise UserError(
                        _('This asset change is already linked to a journal entry! Please post or delete it.'))
                account_period = self.env['ps.account.period'].search(
                    [('date_start', '<', self.date), ('date_end', '>', self.date)])
                for period in account_period:
                    if period.financial_state == 2:
                        raise UserError(_('Date out of account period, can not generate account move!'))
                change_mode = r.alteration_id.change_id
                if r.former_value < r.latter_value:
                    credit_account_id = r.former_category_id.account_asset_id.id
                    debit_account_id = change_mode.account_change_id.id
                elif r.former_value > r.latter_value:
                    credit_account_id = change_mode.account_change_id.id
                    debit_account_id = r.former_category_id.account_asset_id.id
                else:
                    raise UserError(_('The asset value has not changed, can not generate account move!'))
                company_currency = self.company_id.currency_id.id
                # current_currency = self.currency_id
                amount = abs(r.latter_value - r.former_value)
                asset_name = r.asset_id.name
                move_line_credit = {
                    'name': asset_name,
                    'account_id': credit_account_id,
                    'debit': 0.0,
                    'credit': amount,
                    'journal_id': change_mode.journal_id.id,
                    # 'partner_id': self.partner_id.id if self.partner_id else None,
                    'analytic_account_id': False,
                    'currency_id': company_currency or False,
                    'amount_currency': - 1.0 * amount or 0.0,
                }
                move_line_debit = {
                    'name': asset_name,
                    'account_id': debit_account_id,
                    'credit': 0.0,
                    'debit': amount,
                    'journal_id': change_mode.journal_id.id,
                    # 'partner_id': self.partner_id.id if self.partner_id else None,
                    'analytic_account_id': False,
                    'currency_id': company_currency or False,
                    'amount_currency': amount or 0.0,
                }
                move_vals = {
                    'ref': self.name,
                    'date': self.create_date or False,
                    'journal_id': r.alteration_id.change_id.journal_id.id,
                    'line_ids': [(0, 0, move_line_credit), (0, 0, move_line_debit)],
                }

                move = self.env['account.move'].create(move_vals)
                r.write({
                    'move_id': move.id,
                    'is_journal': True
                })
                r.asset_id.write({
                    'move_id': move.id,
                    'is_journal': True
                })
                r.state = 'posted'
            self.write({'state': 'posted'})
        else:
            raise UserError(_('The asset value has not changed, can not generate account move!'))

    @api.multi
    def unlink(self):
        for r in self:
            if r.state != 'draft':
                raise ValidationError(_('Asset Alteration ') + r.name + _(' is not draft, can not delete.'))
        return super(PsAssetAlteration, self).unlink()

    @api.onchange('is_category')
    def _set_detail_is_category(self):
        for r in self.line_ids:
            r.is_category = self.is_category

    @api.onchange('is_asset_state')
    def _set_detail_is_asset_state(self):
        for r in self.line_ids:
            r.is_asset_state = self.is_asset_state

    @api.onchange('is_location')
    def _set_detail_is_location(self):
        for r in self.line_ids:
            r.is_location = self.is_location

    @api.onchange('is_quantity')
    def _set_detail_is_quantity(self):
        for r in self.line_ids:
            r.is_quantity = self.is_quantity
        if not self.is_quantity:
            for r in self.line_ids:
                r.latter_quantity = 0

    @api.onchange('is_value')
    def _set_detail_is_value(self):
        self.is_salvage_value = self.is_value
        for r in self.line_ids:
            r.is_value = self.is_value
            r.is_salvage_value = self.is_value
        if not self.is_value:
            for r in self.line_ids:
                r.latter_value = 0

    @api.onchange('is_init_total')
    def _set_detail_is_init_total(self):
        for r in self.line_ids:
            r.is_init_total = self.is_init_total
        if not self.is_init_total:
            for r in self.line_ids:
                r.latter_depreciation = 0

    @api.onchange('is_salvage_value')
    def _set_detail_is_salvage_value(self):
        for r in self.line_ids:
            r.is_salvage_value = self.is_salvage_value

    @api.onchange('is_method_number')
    def _set_detail_is_method_number(self):
        for r in self.line_ids:
            r.is_method_number = self.is_method_number


class PsAssetAlterationLine(models.Model):
    _name = 'ps.asset.alteration.line'
    _description = 'Asset Alteration Line'

    alteration_id = fields.Many2one('ps.asset.alteration', string='Alteration', requird=True)    #变动ID
    asset_id = fields.Many2one('account.asset.asset', string='Asset', requird=True)    #资产ID
    asset_code = fields.Char(string='Asset Code', related='asset_id.code')    #资产编号

    former_category_id = fields.Many2one('account.asset.category', string='Former Category')    #变更前类型
    latter_category_id = fields.Many2one('account.asset.category', string='Latter Category')    #变更后类型
    former_location_id = fields.Many2one('ps.asset.location', string='Former Location')    #变更前位置
    latter_location_id = fields.Many2one('ps.asset.location', string='Latter Location')    #变更后位置
    former_asset_state_id = fields.Many2one('ps.asset.state', string='Former State')    #变更前状态
    latter_asset_state_id = fields.Many2one('ps.asset.state', string='Latter State')    #变更后状态
    former_quantity = fields.Integer(string='Former Quantity')    #变更前数量
    latter_quantity = fields.Integer(string='Latter Quantity')    #变更后数量
    former_value = fields.Float(string='Former Value')    #变更前原值
    latter_value = fields.Float(string='Latter Value')    #变更后原值
    former_depreciation = fields.Float(string='Former Accumulated Depreciation')    #变更前累计折旧
    latter_depreciation = fields.Float(string='Latter Accumulated Depreciation')    #变更后累计折旧
    former_salvage_value = fields.Float(string='Former Salvage Value')    #变更前净残值
    latter_salvage_value = fields.Float(string='Latter Salvage Value')    #变更后净残值
    former_method_number = fields.Integer(string='Former Method Number')    #变更前使用月数
    latter_method_number = fields.Integer(string='Latter Method Number')    #变更后使用月数

    cause = fields.Char(string='Change Cause', requird=True)  # 变更原因
    is_journal = fields.Boolean(string='Is Generation Voucher', default=True, requird=True)    #是否已生成凭证
    move_id = fields.Many2one('account.move', string='Change Voucher')    #变动凭证
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('posted', 'Posted')
    ], 'Status', default='draft', required=True)    #状态
    is_category = fields.Boolean(string='Is Alter Category', default=False)    #是否变更类型
    is_asset_state = fields.Boolean(string='Is Alter Asset State', default=False)    #是否变更状态
    is_location = fields.Boolean(string='Is Alter Location', default=False)    #是否变更位置
    is_quantity = fields.Boolean(string='Is Alter Quantity', default=False)    #是否变更数量
    is_value = fields.Boolean(string='Is Alter Value', default=False)    #是否变更原值
    is_init_total = fields.Boolean(string='Is Alter Init Total', default=False)    #是否变更累计折旧
    is_salvage_value = fields.Boolean(string='Is Alter Salvage Value', default=False)    #是否变更净残值
    is_method_number = fields.Boolean(string='Is Alter Method Number', default=False)    #是否变更预计使用月数

    @api.onchange('asset_id')
    def on_change_asset_id(self):
        self.former_category_id = self.asset_id.category_id
        self.former_location_id = self.asset_id.ps_location_id
        self.former_asset_state_id = self.asset_id.ps_asset_state_id
        self.former_quantity = self.asset_id.ps_asset_quantity
        self.former_value = self.asset_id.value
        self.former_depreciation = self.asset_id.ps_depreciation_amount
        self.former_salvage_value = self.asset_id.salvage_value
        self.former_method_number = self.asset_id.method_number

        self.is_category = self.alteration_id.is_category
        self.is_asset_state = self.alteration_id.is_asset_state
        self.is_location = self.alteration_id.is_location
        self.is_quantity = self.alteration_id.is_quantity
        self.is_value = self.alteration_id.is_value
        self.is_salvage_value = self.alteration_id.is_value
        self.is_init_total = self.alteration_id.is_init_total
        self.is_method_number = self.alteration_id.is_method_number

    @api.onchange('latter_value')
    def on_change_latter_value(self):
        self.latter_salvage_value = self.latter_value * self.asset_id.category_id.ps_net_salvage_rate / 100









