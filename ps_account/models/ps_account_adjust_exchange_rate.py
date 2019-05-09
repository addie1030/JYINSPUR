# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PsAdjustmentOfExchangeRateLine(models.TransientModel):
    _name = 'ps.adjustment.exchange.rate.line'
    _description = 'Ps Adjustment Exchange Rate Line'

    name = fields.Char(string='name')
    currency_id = fields.Many2one('res.currency', string="Currency Id")  # 币种
    exchange_rate = fields.Float(string="Final Adjust Rate")  # 调整汇率
    fixed_rate = fields.Float(string="Fixed rate")  # 固定汇率
    paer_id = fields.Many2one('ps.adjustment.exchange.rate')


class PsAdjustmentOfExchangeRate(models.TransientModel):
    _name = 'ps.adjustment.exchange.rate'
    _description = 'Ps Adjustment Exchange Rate'
    _rec_name = 'accounting_period'

    accounting_period = fields.Many2one('ps.account.period', string='Accounting Period',
                                        default=lambda self: self.env['ps.account.period'].search(
                                            [('financial_state', '=', '1')]))  # 会计期间
    journal_id = fields.Many2one('account.journal', string='Account Journal Type')  # 账簿类型
    currency_fixed_rate_ids = fields.One2many('ps.adjustment.exchange.rate.line', 'paer_id',
                                              string='Foreign Currency')  # 外币
    accounting_foreign_currency = fields.Many2many('account.account', string='Accounting Foreign Currency',
                                                   domain="[('currency_id', '!=', False)]")  # 核算外币科目
    adjust_date = fields.Date(string='Adjust Date', default=fields.Date.context_today)  # 凭证日期

    @api.multi
    def _compute_currency(self):
        self.account_amount = {}  # 记录科目id以及金额
        self.currency_ids = []  # 记录需要调汇的外币id
        date_start = self.accounting_period.date_start
        date_end = self.accounting_period.date_end
        # TODO 凭证过滤条件应该增加('state', '=', 'posted')
        account_moves = self.env['account.move'].search(
            [('date', '>=', date_start), ('date', '<=', date_end), ('state', '=', 'posted')])
        account_ids = []
        # 将生成调汇页面选择的需要调汇的科目的id放入列表
        for account in self.accounting_foreign_currency:
            account_ids.append(account.id)
        # 找出对应调汇科目的凭证，并且外币金额应该是大于0的凭证
        # main_currency = 0  # 本位币金额
        for account_move in account_moves:
            for line in account_move.line_ids:
                if line.account_id.id in account_ids:
                    if line.account_id.currency_id.id not in self.currency_ids:
                        self.currency_ids.append(line.account_id.currency_id.id)
                    if line.account_id.id not in self.account_amount:
                        self.account_amount.update({line.account_id.id: {
                            'account_id': line.account_id.id,  # 第一次创建记录account_id
                            'local_currency': line.debit if line.debit != 0 else line.credit,
                            'foreign_currency': line.amount_currency,
                            'currency_id': line.account_id.currency_id.id  # 第一次创建记录币种
                        }})
                    else:
                        self.account_amount[line.account_id.id][
                            'local_currency'] += line.debit if line.debit != 0 else line.credit
                        self.account_amount[line.account_id.id]['foreign_currency'] += line.amount_currency
                    continue  # 只记录一次科目和金额，防止金额重复
        return [{'account_amount': self.account_amount},
                {'currency_ids': self.currency_ids}]

    @api.onchange('accounting_period', 'accounting_foreign_currency')
    def update_currency_list(self):
        date_start = self.accounting_period.date_start
        # 生成调汇行
        # self.currency_fixed_rate_ids.unlink()
        currency_ids = self._compute_currency()[1]['currency_ids']
        val = []
        for currency_id in currency_ids:
            currency_name = self.env['res.currency'].search([('id', '=', currency_id)]).name
            exchange_rate = self.env['ps.res.currency.fixed.rate'].search(
                [('currency_id', '=', currency_id), ('name', '=', str(date_start)[5:7])])
            val.append((0, 0, {
                'name': currency_name,
                'currency_id': currency_id,
                'fixed_rate': exchange_rate.account_rate,
                'exchange_rate': exchange_rate.adjust_rate,
            }))
        self.currency_fixed_rate_ids = val

    @api.multi
    def _create_account_move(self, account_amount, currency_rates):
        account_move = self.env['account.move']
        # 生成凭证头
        move = account_move.create({
            'journal_id': self.env.user.company_id.currency_exchange_journal_id.id,
            'date': self.adjust_date,
            'ps_attachcount': 0,
            'create_uid': self.env.user.id,
        })
        for adjust_account in account_amount:
            account_account = self.env['account.account'].search(
                [('id', '=', adjust_account)])
            # 当前科目的借贷方向
            balance_direction = account_account.ps_balance_direction
            for currency_rate in currency_rates:
                if currency_rate['currency_id'].id == account_amount[adjust_account]['currency_id']:
                    rate = currency_rate['rate']
            # 差额
            difference = account_amount[adjust_account]['foreign_currency'] * rate - account_amount[adjust_account][
                'local_currency']
            if difference == 0:
                raise ValidationError(
                    _('The difference is equal to zero and no foreign exchange adjust is required.'))  # 差额为0不需要进行期末调汇
            # 生成凭证行
            val = []
            if balance_direction == '1':
                # 差额大于0
                if difference > 0:
                    # 借方科目
                    val.append((0, 0, {
                        'amount_currency': 0,
                        'name': '汇兑损益',
                        'account_id': adjust_account,
                        'debit': difference,
                        'credit': 0,
                        'ref': move.name,
                        'date_maturity': move.date,
                    }))
                    # 贷方科目
                    val.append((0, 0, {
                        'amount_currency': 0,
                        'name': '汇兑损益',
                        'account_id': self.env.user.company_id.currency_exchange_journal_id.default_credit_account_id.id,
                        'debit': 0,
                        'credit': difference,
                        'ref': move.name,
                        'date_maturity': move.date,
                    }))
                # 差额小于0
                else:
                    # 借方科目
                    val.append((0, 0, {
                        'amount_currency': 0,
                        'name': '汇兑损益',
                        'account_id': self.env.user.company_id.currency_exchange_journal_id.default_debit_account_id.id,
                        'debit': difference,
                        'credit': 0,
                        'ref': move.name,
                        'date_maturity': move.date,
                    }))
                    # 贷方科目
                    val.append((0, 0, {
                        'amount_currency': 0,
                        'name': '汇兑损益',
                        'account_id': adjust_account,
                        'debit': 0,
                        'credit': difference,
                        'ref': move.name,
                        'date_maturity': move.date,
                    }))
            # 科目借贷方向为贷方
            elif balance_direction == '2':
                if difference > 0:
                    # 借方科目
                    val.append((0, 0, {
                        'amount_currency': 0,
                        'name': '汇兑损益',
                        'account_id': self.env.user.company_id.currency_exchange_journal_id.default_debit_account_id.id,
                        'debit': difference,
                        'credit': 0,
                        'ref': move.name,
                        'date_maturity': move.date,
                    }))
                    # 贷方科目
                    val.append((0, 0, {
                        'amount_currency': 0,
                        'name': '汇兑损益',
                        'account_id': adjust_account,
                        'debit': 0,
                        'credit': difference,
                        'ref': move.name,
                        'date_maturity': move.date,
                    }))
                else:
                    # 借方科目
                    val.append((0, 0, {
                        'amount_currency': 0,
                        'name': '汇兑损益',
                        'account_id': adjust_account,
                        'debit': difference,
                        'credit': 0,
                        'ref': move.name,
                        'date_maturity': move.date,
                    }))
                    # 贷方科目
                    val.append((0, 0, {
                        'amount_currency': 0,
                        'name': '汇兑损益',
                        'account_id': self.env.user.company_id.currency_exchange_journal_id.default_credit_account_id.id,
                        'debit': 0,
                        'credit': difference,
                        'ref': move.name,
                        'date_maturity': move.date,
                    }))
            # 未设置借贷方向，提示错误
            else:
                raise ValidationError('科目{}未设置借贷方向，无法进行期末调汇'.format((account_account.code + account_account.name)))
            move.line_ids = val

    @api.multi
    def post(self):
        result = self._compute_currency()
        account_amount = result[0]['account_amount']
        # 币种id 和 汇率
        currency_rates = []
        for rec in self:
            if not rec.currency_fixed_rate_ids:
                raise ValidationError(_('No subject requiring final remittance'))  # 没有需要进行期末调汇的科目
            for line in rec.currency_fixed_rate_ids:
                currency_rates.append({'currency_id': line.currency_id, 'rate': line.exchange_rate})
        self._create_account_move(account_amount, currency_rates)
