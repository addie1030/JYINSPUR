# -*- coding: utf-8 -*-

import time
import math

from datetime import date, datetime
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools
from odoo.addons import decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero

class PsAccountMove(models.Model):
    _inherit = 'account.move'

    line_ids = fields.One2many('account.move.line', 'move_id', string=_('Journal Items'),
                               states={'checked': [('readonly', True)], 'posted': [('readonly', True)]}, copy=True)
    # state = fields.Selection([('draft', _('Created')), ('checked', _('Confirmed')), ('posted', _('Posted'))], string=_('Status'),
    state = fields.Selection([('draft', 'Created'), ('checked', 'Confirmed'), ('posted', 'Posted')], string=_('Status'),
        required=True, readonly=True, copy=False, default='draft',
        help=_('All manually created new journal entries are usually in the status \'Unposted\', '
           'but you can set the option to skip that status on the related journal. '
           'In that case, they will behave as journal entries automatically created by the '
           'system on document validation (invoices, bank statements...) and will be created '
           'in \'Posted\' status.'))
    create_uid = fields.Many2one('res.users', string=_('Created User'))
    ps_confirmed_user = fields.Many2one('res.users', string=_('Confirmed User'))
    ps_posted_user = fields.Many2one('res.users', string=_('Posted User'))
    ps_attachcount = fields.Integer(string=_('Number of Attachments'))
    ps_period_code = fields.Many2one('ps.account.period', string=_('Period number'))
    ps_voucher_name = fields.Char(string=_('Voucher Type'), compute='_set_ps_voucher_name', store=True)
    ps_confirmed_datetime = fields.Date(string=_('Review Time'))
    ps_posted_datetime = fields.Date(string=_('Accounting Time'))
    ps_voucher_word = fields.Char(string=_('Voucher Word'), compute='_set_voucher_no', store=True)
    ps_move_origin = fields.Char(string=_('Source of Voucher'))

    @api.onchange('date')
    def _set_context_date(self):
        self.with_context({'account_move_date': self.date})

    @api.depends('journal_id')
    def _set_ps_voucher_name(self):
        # self.ensure_one()
        for r in self:
            if r.journal_id:
                if r.journal_id.code:
                    r.ps_voucher_name = r.journal_id.ps_voucher_name


    @api.depends('journal_id')
    def _set_voucher_no(self):
        # self.ensure_one()
        for r in self:
            if r.journal_id:
                if r.journal_id.ps_voucher_word:
                    r.ps_voucher_word = r.journal_id.ps_voucher_word


    #获取并设置凭证编号
    # @api.depends('journal_id')
    def _get_set_account_move_ref_name(self, ps_voucher_word, date):
        pap = self.env['ps.account.period'].search([('date_start', '<=', date), ('date_end', '>=', date)])
        period = pap.period
        year = pap.year
        padn = self.env['ps.account.document.no'].search([('year', '=', year),
                                                                      ('period', '=', period),
                                                                      ('voucher_name', '=', ps_voucher_word)])
        if padn:
            voucher_no = str(ps_voucher_word) + '-' + str(padn.voucher_no)
            voucher_no_new = str(int(padn.voucher_no) + 1).zfill(5)
            padn.write({'voucher_no': voucher_no_new})
        else:
            voucher_no = str(ps_voucher_word) + '-' + str(1).zfill(5)
            voucher_no_new = str(2).zfill(5)
            vals = {
                            'period': period,
                            'year': year,
                            'voucher_name': ps_voucher_word,
                            'voucher_no': voucher_no_new,
                            'date': date,
                            'company_id': self.env.user.company_id.id
                        }
            self.env['ps.account.document.no'].create(vals)
        return voucher_no

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        period_ids = self.env['ps.account.period'].get_period(self.date)
        if period_ids[0].financial_state == '2':
            raise ValidationError(str(self.date) + _(' The current date is already in the month, please change the date of the order.'))
        # default = dict(default or {})
        # default.setdefault('code', _("%s (copy)") % (self.code or ''))
        return super(PsAccountMove, self).copy(default)

    def open_win(self):
        self.env['account.move.line'].open_auxiliary_window()

    @api.model
    def create(self, vals):
        vals['create_uid'] = self.env.user.id
        move = super(PsAccountMove,
                     self.with_context(check_move_validity=False, journal_id=vals.get('journal_id'),
                                       partner_id=vals.get('partner_id'))).create(vals)
        move.assert_balanced()
        period_ids = self.env['ps.account.period'].get_period(move.date)

        if not period_ids:
            raise ValidationError(_('Not getting the current accounting period, please maintain.'))
        if len(period_ids) > 1:
            raise ValidationError(_('Duplicate accounting period, please handle.'))
        if period_ids[0].financial_state == '2':
            raise ValidationError(str(move.date) + _(' The current date is already in the month, please change the date of the order.'))
        move.ps_period_code = period_ids[0].id

        manual_move = self.env.context.get('manual_move')

        if move.name == _("Opening Journal Entry"):
            curr_date = self.env['ps.account.period'].search([('financial_state', '=', '1')]).date_start
            move.write({'ref': 'QC', 'name': '00000', 'date': curr_date})
        else:
            no = self._get_set_account_move_ref_name(move.ps_voucher_word, move.date)
            if move.name == _("Profit and loss transfer certificate"):
                move.write({'ref': _('Profit and loss transfer certificate'), 'name': no})
            else:
                if manual_move == '1':
                    move.write({'ref': no, 'name': no})
                else:
                    move.write({'name': no})

        ##*************2018.10.14************
        if self.env.context.get('stock_move_id'):  # 处理单条
            stockmove = self.env['stock.move'].search([('id', '=', self.env.context.get('stock_move_id'))])
            pspv = self.env['ps.stock.picking.view'].search(
                [('stock_picking_id', '=', self.env.context.get('stock_move_id'))])
            if stockmove:
                stockmove.with_context(stock_move_id=0).write({'account_move_id': move.id})
                move.write({'ps_move_origin': 'stock_move'})
            if pspv:
                pspv.write({'ref': no})
            return move
        if self.env.context.get('stock_move_ids'):  # 处理合并
            stockmoves = self.env['stock.move'].search([('id', 'in', self.env.context.get('stock_move_ids'))])
            pspvs = self.env['ps.stock.picking.view'].search(
                [('stock_picking_id', 'in', self.env.context.get('stock_move_ids'))])
            if stockmoves:
                stockmoves.with_context(stock_move_ids=None).write({'account_move_id': move.id})
                move.write({'ps_move_origin': 'stock_move'})
            if pspvs:
                pspvs.write({'ref': no})
            return move
        return move
        ##*************2018.10.14 END ************

    def _get_active_id(self):
        id = 0
        state = ''
        param = {}
        context = self._context
        param = context.get('params')
        if param:
            for k in param:
                if k == 'id':
                    id = param[k]
        if id:
            state = self.search([('id', '=', id)]).state

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):

        res = super(PsAccountMove, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            # 删掉state=‘old’的记录
            delset = self.env['ps.account.move.line.sub'].search([('state', '=', 'old')])
            dels = []
            if delset:
                for r in delset:
                    dels.append(r.id)
                    self._cr.execute(""" Delete From ps_account_move_line_sub WHERE id = %s """, tuple(dels))
                    del dels[0]
        return res

    @api.model
    def get_pz_view_id(self):
        view_id = self.env.ref('ps_account.view_move_tree_new').id
        view_form_id = self.env.ref('account.view_move_form').id
        search_view_id = self.env.ref('account.view_account_move_filter').id,
        return view_id, search_view_id, view_form_id

    @api.multi
    def unlink(self):
        for r in self:
            if r.ps_move_origin == "stock_move":
                if r.stock_move_id:
                    r.stock_move_id.write({'account_move_id': None})

        return super(PsAccountMove, self).unlink()


class PsAccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _order = "date asc, id asc"

    name = fields.Char(string="Label")
    ps_is_sub = fields.Boolean(default=False, string=_('Whether it is auxiliary accounting'))
    ps_sub_id = fields.Many2one('ps.account.move.line.sub', string=_('Auxiliary accounting'))
    main_auxiliary_id = fields.Integer(string=_('Auxiliary accounting master table ID'), default=0)

    ps_unit_price = fields.Float(digits=dp.get_precision('ps_unit_price'), string=_('Unit price'))
    ps_currency_rate = fields.Float(digits=dp.get_precision('ps_unit_price'), string=_('Exchange rate'))
    ps_amount = fields.Float(digits=(16, 2), string=_('Amount'))
    cash_flow_item_id = fields.Many2one('ps.cashflow.item', string=_("Cash Flow Line"))
    ps_check_sub_fail = fields.Boolean(default=False)

    @api.onchange('debit', 'credit')
    def _set_round_debit_credit(self):
        for r in self:
            r.debit = round(r.debit, 2)
            r.credit = round(r.credit, 2)


    @api.model
    def default_get(self, fields):
        rec = super(PsAccountMoveLine, self).default_get(fields)
        if 'line_ids' not in self._context:
            return rec

        # compute the default credit/debit of the next line in case of a manual entry
        balance = 0
        name = ''
        for line in self._context['line_ids']:
            if line[2]:
                balance += line[2].get('debit', 0) - line[2].get('credit', 0)
                name = line[2].get('name')
        if balance < 0:
            rec.update({'debit': -balance})
        if balance > 0:
            rec.update({'credit': balance})
        rec.update({'name': name})
        return rec

    @api.onchange('account_id')
    def _alter_ps_analytic_boolean(self):
        self.ensure_one()
        if self.account_id.ps_auxiliary_state == '1':
            self.ps_is_sub = True
        else:
            self.ps_sub_id = 0
            self.ps_is_sub = False

    @api.onchange('ps_sub_id')
    def _set_auxiliary_value(self):
        for r in self:
            if r.ps_sub_id.ps_consider_partner:
                r.partner_id = r.ps_sub_id.ps_consider_partner.id
            else:
                r.partner_id = 0
            if r.ps_sub_id.ps_consider_product:
                r.product_id = r.ps_sub_id.ps_consider_product.id
            else:
                r.product_id = 0
            if r.ps_sub_id.cash_flow_item_id:
                r.cash_flow_item_id = r.ps_sub_id.cash_flow_item_id.id
            else:
                r.cash_flow_item_id = 0

    @api.model_cr
    def init(self):
        res = super(PsAccountMoveLine, self).init()
        cr = self._cr
        cr.execute(
            "SELECT constraint_name from information_schema.table_constraints where table_name='account_move_line' and constraint_name = %s",
            ('account_move_line_credit_debit2',))
        if cr.fetchone():
            cr.execute(
            'alter table account_move_line DROP CONSTRAINT account_move_line_credit_debit2')
        return res

    @api.model
    def create(self, vals):
        paa = self.env['ps.account.move.line.sub']
        new_lines = super(PsAccountMoveLine, self).create(vals)
        for r in new_lines:
            if r.ps_sub_id:
                paa.with_context({'auxiliary_account_id': r.account_id.id})
                paa.search([('id', '=', r.ps_sub_id.id)]).write(
                    {'state': 'used', 'account_id': r.account_id.id, 'move_line_id': r.id})
                if r.ps_sub_id.analytic_line_ids:
                    for aal in r.ps_sub_id.analytic_line_ids:
                        aal.write({'move_id': r.id})

                if r.ps_sub_id.ps_consider_currency.id:  # 设置外币金额 外币借方金额，外币借方数量，外币贷方金额，外币贷方数量
                    r.write({'amount_currency': r.ps_sub_id.amount_input,'currency_id': r.ps_sub_id.ps_consider_currency.id})
                    if abs(r.debit) > 0 and abs(r.ps_sub_id.ps_consider_quantity) > 0:
                        r.write({'quantity': r.ps_sub_id.ps_consider_quantity})
                    elif abs(r.credit) > 0 and abs(r.ps_sub_id.ps_consider_quantity) > 0:
                        r.write({'quantity': r.ps_sub_id.ps_consider_quantity})
                if r.ps_sub_id.ps_consider_partner:  # 核算往来单位
                    r.write({'partner_id': r.ps_sub_id.ps_consider_partner.id})
                if r.ps_sub_id.ps_consider_product:  # 核产品
                    r.write({'product_id': r.ps_sub_id.ps_consider_product.id})
                    # 核算数量
                    r.write({'quantity': r.ps_sub_id.ps_consider_quantity})
                if r.ps_sub_id.cash_flow_item_id:  # 现金流量
                    r.write({'cash_flow_item_id': r.ps_sub_id.cash_flow_item_id.id})
            else:
                vals_aux = {}
                if r.account_id.ps_auxiliary_state:
                    r.write({'ps_is_sub': True})
                else:
                    r.write({'ps_is_sub': False})
                if r.currency_id:  # 外币
                    vals_aux['ps_consider_currency'] = r.currency_id.id
                    if abs(r.amount_currency) > 0:  # 外币金额
                        vals_aux['currency_amount'] = r.amount_currency
                if r.account_id.ps_consider_product:
                    if abs(r.quantity) > 0:  # 数量
                        r.write({'ps_is_sub': True})
                        vals_aux['ps_consider_quantity'] = r.quantity
                        rec = self.env['account.invoice.line'].search([('invoice_id', '=', r.invoice_id.id),
                                                                 ('product_id', '=', r.product_id.id)])
                        if rec:
                            vals_aux['unit_price'] = rec.price_unit
                if abs(r.debit) > 0:
                    vals_aux['amount'] = r.debit
                if abs(r.credit) > 0:
                    vals_aux['amount'] = r.credit
                if r.account_id.ps_consider_partner:
                    if r.partner_id:  # 往来单位
                        r.write({'ps_is_sub': True})
                        vals_aux['ps_consider_partner'] = r.partner_id.id
                if r.account_id.ps_consider_product:
                    if r.product_id:  # 产品
                        r.write({'ps_is_sub': True})
                        vals_aux['ps_consider_product'] = r.product_id.id
                    if r.product_uom_id:  # 单位
                        r.write({'ps_is_sub': True})
                        vals_aux['product_uom_id'] = r.product_uom_id.id
                if r.account_id.ps_is_cash_flow:
                    if r.cash_flow_item_id:  # 现金流量
                        r.write({'ps_is_sub': True})
                        vals_aux['cash_flow_item_id'] = r.cash_flow_item_id.id
                vals_aux['move_line_id'] = r.id
                vals_aux['state'] = 'used'
                vals_aux['account_id'] = r.account_id.id
                rec = paa.create(vals_aux)
                r.write({'ps_sub_id': rec.id})  # 更新分录表的辅助核算记录ID
                vals_aux.clear()

        return new_lines

    @api.multi
    def write(self, vals):
        if not self.env.context.get('move_warn_color') == '1':
            vals['ps_check_sub_fail'] = False
        if self.env.context.get('check_post_write') == '1' or self.env.context.get(
                'background_code_generate_asset') == '1':
            return super(PsAccountMoveLine, self).write(vals)
        else:
            if vals.get('ps_sub_id'):
                rec = self.env['ps.account.move.line.sub'].search([('id', '=', vals['ps_sub_id'])])
                if rec.state != 'used':
                    rec.write({'state': 'used'})
                if rec.ps_consider_partner:
                    vals['partner_id'] = rec.ps_consider_partner.id
                if rec.ps_consider_product:
                    vals['product_id'] = rec.ps_consider_product.id
        return super(PsAccountMoveLine, self).write(vals)

    @api.multi
    @api.constrains('currency_id', 'account_id')
    def _check_currency(self):
        pass
        # i = 1
        # for line in self:
        #     account_currency = line.account_id.currency_id
        #     if account_currency:#有外币核算
        #         if not line.currency_id:#分录没有核算外币
        #             raise ValidationError('第 ' + str(i) + ' 行外币核算不能为空.')
        #     i = i + 1

    #检查限制类型
    # @api.multi
    # @api.constrains('account_id')
    def _check_ps_control_style(self, debit, credit, account_id, journal_id):
        aj = self.env['account.journal'].search([('id', '=', journal_id)])
        account = self.env['account.account'].search([('id', '=', account_id)])
        sname = ''
        if aj:
            if aj.ps_control_style == '0':
                pass
            elif aj.ps_control_style == '1':#借方必有
                if abs(debit) > 0:
                    if aj.ps_control_account_ids:
                        if not (account in aj.ps_control_account_ids):
                            for r in aj.ps_control_account_ids:
                                sname = sname + ' ' + r.name
                            raise ValidationError(_('Current account book【') + aj.name + _('】, Debit account must contain【')+sname+'】.')
            elif aj.ps_control_style == '2':#贷方必有
                if abs(credit) > 0:
                    if aj.ps_control_account_ids:
                        if not (account in aj.ps_control_account_ids):
                            for r in aj.ps_control_account_ids:
                                sname = sname + ' ' + r.name
                            raise ValidationError(_('Current account book【') + aj.name + _('】, Credit account must contain【')+sname+'】.')
            elif aj.ps_control_style == '3':#借方必无
                if abs(debit) > 0:
                    if aj.ps_control_account_ids:
                        if (account in aj.ps_control_account_ids):
                            for r in aj.ps_control_account_ids:
                                sname = sname + ' ' + r.name
                            raise ValidationError(_('Current account book【') + aj.name + _('】, Debit account cannot contain【')+sname+'】.')
            elif aj.ps_control_style == '4':#贷方必无
                if abs(credit) > 0:
                    if aj.ps_control_account_ids:
                        if (account in aj.ps_control_account_ids):
                            for r in aj.ps_control_account_ids:
                                sname = sname + ' ' + r.name
                            raise ValidationError(_('Current account book【') + aj.name + _('】, Credit account cannot contain【')+sname+'】.')
            elif aj.ps_control_style == '5':#凭证必无
                if aj.ps_control_account_ids:
                    if (account in aj.ps_control_account_ids):
                        for r in aj.ps_control_account_ids:
                            sname = sname + ' ' + r.name
                        raise ValidationError(_('Current account book【') + aj.name + _('】, Account cannot contain【')+sname+'】.')
            elif aj.ps_control_style == '6':#凭证必有
                if aj.ps_control_account_ids:
                    if not (account in aj.ps_control_account_ids):
                        for r in aj.ps_control_account_ids:
                            sname = sname + ' ' + r.name
                        raise ValidationError(_('Current account book【') + aj.name + _('】, Account must contain【')+sname+'】.')

    @api.multi
    def unlink(self):
        if self.env.context.get('auxiliary_style') == '1':
            return super(PsAccountMoveLine, self).unlink()
        else:
            ids = []
            for r in self:
                ids.append(r.ps_sub_id.id)
            if len(ids):
                paa = self.env['ps.account.move.line.sub']
                paa.search([('id', 'in', ids)]).unlink()
            return super(PsAccountMoveLine, self).unlink()

    #检查当前科目与辅助核算是否匹配
    # @api.multi
    # @api.constrains('ps_is_sub')
    def _check_account_auxiliary(self):
        for r in self:
            name = r.account_id.name
            if r.ps_is_sub:
                if not r.ps_sub_id:
                    raise ValidationError(_('【') + name + _('】account has auxiliary accounting, please fill in the auxiliary accounting item..'))
                if r.account_id.consider_currency:
                    r.currency_id = r.ps_sub_id.consider_currency.id
                else:
                    r.currency_id = 0
                    r.ps_sub_id.consider_currency = 0
                if r.account_id.consider_quantity:
                    if not r.ps_sub_id.consider_quantity:
                        raise ValidationError(_('【') + name + _('】 account accounting quantity, please fill in the quantity.'))
                    if not r.ps_sub_id.product_uom_id:
                        raise ValidationError(_('【') + name + _('】 account accounting unit, please select the unit.'))
                    if not r.ps_sub_id.unit_price:
                        raise ValidationError(_('【') + name + _('】 account accounting unit price, please fill in the unit price.'))
                else:
                    r.ps_sub_id.consider_quantity = 0
                    r.quantity = 0
                    r.ps_sub_id.product_uom_id = 0
                    r.product_uom_id = 0
                    r.ps_sub_id.unit_price = 0
                    r.ps_unit_price = 0
                    r.ps_sub_id.amount = 0
                    r.ps_amount = 0
                if r.account_id.ps_consider_partner:
                    if not r.ps_sub_id.ps_consider_partner:
                        raise ValidationError(_('【') + name + _('】 account accounting partner, please select the partner.'))
                else:
                    r.ps_sub_id.ps_consider_partner = 0
                    r.partner_id = 0
                if r.account_id.ps_consider_product:
                    if not r.ps_sub_id.ps_consider_product:
                        raise ValidationError(_('【') + name + _('】account accounting product, please select the product.'))
                else:
                    r.ps_sub_id.ps_consider_product = 0
                    r.product_id = 0


    #有辅助核算的设置借、贷金额
    @api.onchange('ps_sub_id')
    def _set_account_move_line_debit_credit(self):
        self.ensure_one()
        if self.ps_sub_id.id > 0:
            if abs(self.debit) == 0 and abs(self.credit) == 0:
                self.debit = self.ps_sub_id.amount
            elif abs(self.debit) > 0:
                self.debit = self.ps_sub_id.amount
            elif abs(self.credit) > 0:
                self.credit = self.ps_sub_id.amount

    @api.multi
    @api.constrains('account_id')
    def set_ps_is_sub_val(self):
        for r in self:
            if r.account_id.ps_auxiliary_state == '1':
                r.ps_is_sub = True
            else:
                r.ps_is_sub = False


class PsAccountMoveLineSub(models.Model):
    _name = 'ps.account.move.line.sub'
    _description = 'ps.account.move.line.sub'

    name = fields.Char(compute='_create_name', store=True)
    state = fields.Char(string=_('State'), default='old')
    ps_consider_partner = fields.Many2one('res.partner', string=_('Partner'))
    ps_consider_product = fields.Many2one('product.product', string='Product')
    ps_consider_currency = fields.Many2one('res.currency', string='Currency')
    ps_consider_quantity = fields.Float(digits=(16, 2), string='Quantity')
    product_uom_id = fields.Many2one('uom.uom', string='Unit')
    unit_price = fields.Float(digits=(16, 2), string='Unit Price')
    amount = fields.Float(digits=(16, 2), string='Amount', compute='_compute_amount', store=True)
    amount_input = fields.Float(digits=(16, 2), string='Amount', store=True)
    cash_flow_item_id = fields.Many2one('ps.cashflow.item', string=_("Cash Flow Line"))
    account_id = fields.Many2one('account.account')
    opening_sub_id = fields.Many2one('ps.sub.opening')
    debit = fields.Float(digits=(16, 2), string='Debit')
    credit = fields.Float(digits=(16, 2), string='Credit')
    ps_currency_rate = fields.Float(digits=(16, 2), string='Exchange Rate')
    currency_amount = fields.Float(digits=(16, 2), string='Currency Amount')
    move_line_id = fields.Many2one('account.move.line')
    analytic_line_ids = fields.One2many('account.analytic.line', 'move_line_sub_id', string='Analytic Line')
    balance_direction = fields.Selection([('1', '借方'), ('2', '贷方')], string='方向')

    def _get_move_line_id(self):
        return

    @api.onchange('ps_consider_partner',
                  'ps_consider_product', 'ps_consider_currency',
                  'ps_consider_quantity', 'product_uom_id', 'unit_price', 'amount', 'cash_flow_item_id')
    def _set_account_id(self):
        self.ensure_one()
        account_id = self.env.context.get('auxiliary_account_id')
        account = self.env['account.account'].search([('id', '=', account_id)])
        # if account.currency_id:
        #     self.ps_consider_currency = account.currency_id.id
        self.account_id = account_id
        if account.currency_id:
            if self.ps_consider_currency:
                curren_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                month = time.strftime('%Y-%m-%d', time.localtime(time.time()))[5:7]
                currency_id = (self.ps_consider_currency.id,)
                if self.ps_consider_currency.ps_rate_style == '1':
                    self._cr.execute('Select account_rate From ps_res_currency_fixed_rate ' \
                                     'WHERE name <= %s And currency_id = %s Order By name Desc limit 1',
                                     (month, currency_id,))
                elif self.ps_consider_currency.ps_rate_style == '2':
                    self._cr.execute('Select rate From res_currency_rate ' \
                                     'WHERE name <= %s And currency_id = %s Order By name Desc limit 1',
                                     (curren_date, currency_id,))
                L = self._cr.fetchone()
                if L:
                    if len(L):
                        r = L[0]
                        if r != 0:
                            self.ps_currency_rate = r
                        else:
                            self.ps_currency_rate = 0.0

    #处理外币核算、金额计算
    @api.multi
    @api.depends('ps_consider_quantity', 'unit_price', 'amount_input', 'ps_currency_rate')
    def _compute_amount(self):
        account_id = self.env.context.get('auxiliary_account_id')
        account = self.env['account.account'].search([('id', '=', account_id)])

        for r in self:
            if abs(r.ps_consider_quantity):
                ps_consider_quantity = r.ps_consider_quantity
            else:
                ps_consider_quantity = 0
            if abs(r.unit_price):
                unit_price = r.unit_price
            else:
                unit_price = 0
            if ps_consider_quantity and unit_price:
                if r.account_id.currency_id:
                    if r.ps_consider_currency:#核算数量和外币
                        if r.ps_consider_currency.ps_rate_compute_style == '1':#原币*汇率=本位币
                            r.amount = ps_consider_quantity * unit_price * r.ps_currency_rate #本币金额
                        elif r.ps_consider_currency.ps_rate_compute_style == '2':#原币/汇率=本位币
                            r.amount = (ps_consider_quantity * unit_price) / r.ps_currency_rate  # 本币金额
                else:#核算数量不核算外币
                    r.amount = ps_consider_quantity * unit_price
                r.amount_input = ps_consider_quantity * unit_price
            elif abs(r.amount_input):
                if account.currency_id:
                    r.ps_consider_currency = account.currency_id.id
                    if r.ps_consider_currency:
                        if r.ps_consider_currency.ps_rate_compute_style == '1':  # 原币*汇率=本位币
                            r.amount = r.amount_input * r.ps_currency_rate #本币金额
                        elif r.ps_consider_currency.ps_rate_compute_style == '2':  # 原币/汇率=本位币
                            r.amount = r.amount_input / r.ps_currency_rate  # 本币金额
                else:
                    r.amount = r.amount_input #不核算数量也不核算外币

    @api.depends('ps_consider_partner',
                 'ps_consider_product', 'ps_consider_currency',
                 'ps_consider_quantity', 'product_uom_id', 'unit_price', 'amount',
                 'cash_flow_item_id',)
    def _create_name(self):
        # self.ensure_one()
        name9 = ''
        for r in self:
            if r.ps_consider_partner:
                name1 = _('/partner:') + r.ps_consider_partner.name + '\n'
            else:
                name1 = ''
            if r.ps_consider_product:
                name4 = _('/product:') + r.ps_consider_product.name + '\n'
            else:
                name4 = ''
            if r.ps_consider_currency:
                if r.amount_input != 0:
                    name9 = '/' + _('currency amount:') + str(r.amount_input) + '\n'
                else:
                    name9 = ''
                name5 = _('/currency:') + r.ps_consider_currency.name + '\n'
            else:
                name5 = ''
            if r.ps_consider_quantity != 0:
                name6 = _('/quantity:') + str(r.ps_consider_quantity) + '\n'
            else:
                name6 = ''
            if r.product_uom_id:
                name7 = '/' + _('unit:') + r.product_uom_id.name + '\n'
            else:
                name7 = ''
            if r.unit_price > 0:
                name8 = '/' + _('unit price:') + str(r.unit_price) + '\n'
            else:
                name8 = ''

            if r.cash_flow_item_id:
                name20 = '/现金流量:' + r.cash_flow_item_id.name + '\n'
            else:
                name20 = ''

            str_aal = ''
            if r.analytic_line_ids:
                for aal in r.analytic_line_ids:
                    str_aal = str_aal + aal.name + ' /金额：' + str(aal.amount) + '/'

            str1 = (name1 + name4 + name5).lstrip('/')
            str2 = (name6 + name7 + name8 + name9)
            str4 = name20
            str5 = str_aal
            r.name = (str1 + '\n' + str2 + '\n' + str4 + str5).lstrip('/')

    @api.constrains('ps_currency_rate')
    def _check_ps_currency_rate(self):
        account_id = self.env.context.get('auxiliary_account_id')
        account = self.env['account.account'].search([('id', '=', account_id)])
        if account.currency_id:
            for r in self:
                if r.ps_currency_rate <= 0:
                    raise ValidationError(_('This account accounts for foreign currency, please fill in the exchange rate.'))

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PsAccountMoveLineSub, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        account = self.env['account.account'].search([('id', '=', self.env.context.get('auxiliary_account_id'))])
        if account.currency_id:
            ps_consider_currency = True
        else:
            ps_consider_currency = False
        if account.ps_consider_partner:
            ps_consider_partner = True
        else:
            ps_consider_partner = False
        if account.ps_consider_product:
            ps_consider_product = True
            ps_consider_quantity = True
        else:
            ps_consider_product = False
            ps_consider_quantity = False

        if view_type == 'form':
            doc = etree.XML(res['arch'])
            if not ps_consider_currency:
                if doc.xpath("//field[@name='ps_consider_currency']"):
                    node = doc.xpath("//field[@name='ps_consider_currency']")[0]
                    node.set('invisible', '1')
                    node.set('required', '0')
                    setup_modifiers(node, res['fields']['ps_consider_currency'])
                if doc.xpath("//field[@name='ps_currency_rate']"):
                    node = doc.xpath("//field[@name='ps_currency_rate']")[0]
                    node.set('invisible', '1')
                    node.set('required', '0')
                    setup_modifiers(node, res['fields']['ps_currency_rate'])
            if not ps_consider_partner:
                if doc.xpath("//field[@name='ps_consider_partner']"):
                    node = doc.xpath("//field[@name='ps_consider_partner']")[0]
                    node.set('invisible', '1')
                    node.set('required', '0')
                    setup_modifiers(node, res['fields']['ps_consider_partner'])
            if not ps_consider_quantity:
                if doc.xpath("//field[@name='ps_consider_quantity']"):
                    node = doc.xpath("//field[@name='ps_consider_quantity']")[0]
                    node.set('invisible', '1')
                    node.set('required', '0')
                    setup_modifiers(node, res['fields']['ps_consider_quantity'])
                if doc.xpath("//field[@name='unit_price']"):
                    node = doc.xpath("//field[@name='unit_price']")[0]
                    node.set('invisible', '1')
                    node.set('required', '0')
                    setup_modifiers(node, res['fields']['unit_price'])
                if doc.xpath("//field[@name='product_uom_id']"):
                    node = doc.xpath("//field[@name='product_uom_id']")[0]
                    node.set('invisible', '1')
                    node.set('required', '0')
                    setup_modifiers(node, res['fields']['product_uom_id'])
                if ps_consider_currency:#不核算数量，但是核算外币
                    if doc.xpath("//field[@name='amount_input']"):
                        node = doc.xpath("//field[@name='amount_input']")[0]
                        node.set('readonly', '0')
                        node.set('string', _('currency amount'))
                        setup_modifiers(node, res['fields']['amount_input'])
                    if doc.xpath("//field[@name='amount']"):
                        node = doc.xpath("//field[@name='amount']")[0]
                        node.set('string', _('local currency amount'))
                        node.set('readonly', '1')
                        setup_modifiers(node, res['fields']['amount'])
                else:#不核算数量，不核算外币
                    if doc.xpath("//field[@name='amount_input']"):
                        node = doc.xpath("//field[@name='amount_input']")[0]
                        node.set('readonly', '0')
                        node.set('string', _('amount'))
                        setup_modifiers(node, res['fields']['amount_input'])
                    if doc.xpath("//field[@name='amount']"):
                        node = doc.xpath("//field[@name='amount']")[0]
                        node.set('readonly', '0')
                        node.set('invisible', '1')
                        setup_modifiers(node, res['fields']['amount'])
            else:
                if ps_consider_currency:#核算数量和外币
                    if doc.xpath("//field[@name='amount_input']"):
                        node = doc.xpath("//field[@name='amount_input']")[0]
                        node.set('invisible', '0')
                        node.set('readonly', '0')
                        node.set('string', _('currency amount'))
                        setup_modifiers(node, res['fields']['amount_input'])
                    if doc.xpath("//field[@name='amount']"):
                        node = doc.xpath("//field[@name='amount']")[0]
                        node.set('string', _('local currency amount'))
                        node.set('readonly', '1')
                        node.set('invisible', '0')
                        setup_modifiers(node, res['fields']['amount'])
                else:#核算数量，不核算外币
                    if doc.xpath("//field[@name='amount_input']"):
                        node = doc.xpath("//field[@name='amount_input']")[0]
                        node.set('invisible', '1')
                        node.set('readonly', '0')
                        node.set('string', _('amount'))
                        setup_modifiers(node, res['fields']['amount_input'])
                    if doc.xpath("//field[@name='amount']"):
                        node = doc.xpath("//field[@name='amount']")[0]
                        node.set('readonly', '1')
                        node.set('invisible', '0')
                        node.set('string', _('amount'))
                        setup_modifiers(node, res['fields']['amount'])
            if not ps_consider_product:
                if doc.xpath("//field[@name='ps_consider_product']"):
                    node = doc.xpath("//field[@name='ps_consider_product']")[0]
                    node.set('invisible', '1')
                    node.set('required', '0')
                    setup_modifiers(node, res['fields']['ps_consider_product'])
            if not account.ps_is_cash_flow:
                if doc.xpath("//field[@name='cash_flow_item_id']"):
                    node = doc.xpath("//field[@name='cash_flow_item_id']")[0]
                    node.set('invisible', '1')
                    node.set('required', '0')
                    setup_modifiers(node, res['fields']['cash_flow_item_id'])
            if not account.ps_is_account_analytic:
                if doc.xpath("//field[@name='analytic_line_ids']"):
                    node = doc.xpath("//field[@name='analytic_line_ids']")[0]
                    node.set('invisible', '1')
                    setup_modifiers(node, res['fields']['analytic_line_ids'])

            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.multi
    def write(self, vals):
        return super(PsAccountMoveLineSub, self.with_context({'auxiliary_write_id': self.id})).write(vals)

    @api.onchange('ps_consider_product')
    def set_product_uom_id(self):
        if self.ps_consider_product.uom_id:
            self.product_uom_id = self.ps_consider_product.uom_id.id

    @api.onchange('analytic_line_ids')
    def _compute_amount_input(self):
        amount = 0.0
        for r in self.analytic_line_ids:
            if abs(r.amount):
                amount += r.amount
        self.amount_input = amount

    @api.constrains('amount_input', 'analytic_line_ids')
    def _check_amount_input(self):
        for ai in self:
            if ai.analytic_line_ids:
                amount = 0.0
                for r in ai.analytic_line_ids:
                    if abs(r.amount):
                        amount += r.amount
                amount = round(amount, precision_digits=2)
                if ai.amount_input != amount:
                    raise ValidationError(
                        _('The total amount of analytic not equal to amount.'))


class PsAccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    move_line_sub_id = fields.Many2one('ps.account.move.line.sub', string='Move Line Sub')
    tag_id = fields.Many2one('account.analytic.tag', string='Tag',
                             related="ps_account_id.ps_analytic_tag_id")
    ps_account_id = fields.Many2one('account.account')

    @api.onchange('account_id')
    def _set_account_analytic_line_name(self):
        account = self.env['account.account'].browse(self.env.context.get('auxiliary_account_id'))
        for r in self:
            r.ps_account_id = account.id
            if not r.name and r.account_id:
                r.name = r.account_id.name
            if account.ps_analytic_tag_id and r.account_id and not r.tag_id:
                r.tag_id = account.ps_analytic_tag_id.id

    @api.multi
    def unlink(self):
        for r in self:
            if r.move_id:
                raise ValidationError(_('The analytic line cannot be deleted.'))


class PsAccountMoveCheck(models.Model):
    _name = 'ps.account.move.check'
    _description = 'ps.account.move.check'
    _auto = False

    ref = fields.Char(string='Voucher Number')
    date = fields.Date(string='Create Date')
    journal_id = fields.Many2one('account.journal', string='Journal Type')
    state = fields.Selection([('draft', 'Draft'), ('checked', 'Validate'), ('posted', 'Posting')], string='Document Status')
    ps_voucher_name = fields.Char(string='Voucher Type')
    ps_confirmed_user = fields.Many2one('res.users', string='Reviewer')
    ps_confirmed_datetime = fields.Date(string='Reviewer Time')

    name = fields.Char(string="Abstract")
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    account_id = fields.Many2one('account.account', string='Subject')
    ps_sub_id = fields.Many2one('ps.account.move.line.sub', string='Auxiliary Accounting')
    ps_check_sub_fail = fields.Boolean(default=False)

    @api.model_cr
    def init(self):
        self._table = 'ps_account_move_check'
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        create or replace view ps_account_move_check as (
            select min(t2.id) as id,
                   t1.name as ref,
                   t1.date as date,
                   t1.journal_id as journal_id,
                   t1.state as state,
                   t1.ps_voucher_name as ps_voucher_name,
                   t1.ps_confirmed_datetime as ps_confirmed_datetime,
                   t1.ps_confirmed_user as ps_confirmed_user,
                   t1.ps_posted_user as ps_posted_user,
                   t2.name as name,
                   t2.debit as debit,
                   t2.credit as credit,
                   t2.account_id as account_id,
                   t2.ps_sub_id as ps_sub_id,
                   t2.ps_check_sub_fail as ps_check_sub_fail
            from account_move t1, account_move_line t2
            where t1.id = t2.move_id and t1.state in ('draft','checked') and t1.name <> '00000'
            group by t1.name,t1.date,t1.journal_id,t1.state,t1.ps_voucher_name,
                     t2.name,t2.debit,t2.credit,t2.account_id,t2.ps_sub_id,t2.ps_check_sub_fail,
                     t1.ps_confirmed_datetime,t1.ps_confirmed_user,t1.ps_posted_user
            order by t1.date desc
        )
        """)

    # 重写unlink函数
    @api.multi
    def unlink(self):
        for r in self:
            if r.state != 'draft':
                raise ValidationError(_('The voucher【 ') + r.ref + _(' 】is not in "Draft" state and cannot be deleted.'))
            else:
                move_id = self.env['account.move.line'].search([('id', '=', r.id)]).move_id.id
                move_lines = self.env['account.move.line'].search([('move_id', '=', move_id)])
                move = self.env['account.move'].search([('id', '=', move_id)])
                if move_lines:
                    move_lines.unlink()
                if move:
                    move.unlink()


class PsAccountMovePost(models.Model):
    _name = 'ps.account.move.post'
    _description = 'ps.account.move.post'
    _auto = False

    ref = fields.Char(string='Voucher Number')
    date = fields.Date(string='Create Date')
    journal_id = fields.Many2one('account.journal', string='Journal Type')
    state = fields.Selection([('draft', 'Draft'), ('checked', 'Validate'), ('posted', 'Posting')], string='Document Status')
    ps_voucher_name = fields.Char(string='Voucher Type')
    ps_posted_user = fields.Many2one('res.users', string='Bookkeeper')
    ps_posted_datetime = fields.Date(string='Accounting Time')

    name = fields.Char(string="Abstract")
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    account_id = fields.Many2one('account.account', string='Subject')
    ps_sub_id = fields.Many2one('ps.account.move.line.sub', string='Auxiliary Accounting')

    @api.model_cr
    def init(self):
        self._table = 'ps_account_move_post'
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        create or replace view ps_account_move_post as (
            select min(t2.id) as id,
                   t1.name as ref,
                   t1.date as date,
                   t1.journal_id as journal_id,
                   t1.state as state,
                   t1.ps_voucher_name as ps_voucher_name,
                   t1.ps_posted_datetime as ps_posted_datetime,
                   t1.ps_posted_user as ps_posted_user,
                   t2.name as name,
                   t2.debit as debit,
                   t2.credit as credit,
                   t2.account_id as account_id,
                   t2.ps_sub_id as ps_sub_id
            from account_move t1, account_move_line t2
            where t1.id = t2.move_id and t1.state in ('posted','checked') and t1.name <> '00000'
            group by t1.name,t1.date,t1.journal_id,t1.state,t1.ps_voucher_name,
                     t2.name,t2.debit,t2.credit,t2.account_id,t2.ps_sub_id,
                     t1.ps_posted_datetime,t1.ps_posted_user
            order by t1.date desc
        )
        """)

    # 重写unlink函数
    @api.multi
    def unlink(self):
        for r in self:
            raise ValidationError(_('The voucher【 ') + r.ref + _(' 】is not in "Draft" state and cannot be deleted.'))



