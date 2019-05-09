# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


# 自定义结转凭证生成向导
class PsAccountCarryOverCreate(models.Model):
    _name = "ps.account.carry.over.create"
    _description = "Ps Account Carry Over Create"

    period_id = fields.Many2one('ps.account.period', string='Period Of Voucher Generation',
                                domain=[('financial_state', 'in', ['1', '0'])],
                                default=lambda self: self.env['ps.account.period'].search(
                                    [('financial_state', '=', '1')]))  # 期间
    journal_id = fields.Many2one('account.journal', string='Account Journal')  # 日记账
    account_carry_over_ids = fields.One2many('ps.account.carry.over.head', 'carry_over_create_id',
                                             string='Carry Over Template',
                                             default=lambda self: self.env['ps.account.carry.over.head'].search(
                                                 []))  # 自定义结转模版

    @api.multi
    def _get_move_lines(self):
        """ 根据取数规则实现取数逻辑 """
        new_move = {}  # 存储生成一个凭证的数据
        for res in self:
            for carry_over_head in res.account_carry_over_ids:
                # 选择勾选到的条目
                new_lines = {}  # 存储多条分录数据
                if carry_over_head.is_generate:
                    # 以下为取数逻辑
                    for move in carry_over_head.move_ids:
                        new_move_line = {}  # 存储生成一条凭证分录的数据
                        quantity = 0
                        amount = 0
                        if move.take_other_total:  # 取对方科目合计
                            amount_ratio = 0
                        for amount_rule in move.rule_amount_ids:
                            account_ids = []  # 记录符合条件的科目id
                            currency_id = amount_rule.currency_id.id  # 币种ID
                            # 截取科目编号，并进行模糊查询
                            if amount_rule.account_substr:
                                account_substr = int(amount_rule.account_substr)  # 科目位数
                                account_no = amount_rule.account_no[0: account_substr] + '%'  # 截取科目编号
                                for account_id in self.env['account.account'].search(
                                        [('code', 'like', account_no), ('currency_id', '=', currency_id)]):
                                    account_ids.append(account_id.id)
                            else:
                                account_no = amount_rule.account_no
                                for account_id in self.env['account.account'].search(
                                        [('code', '=', account_no), ('currency_id', '=', currency_id)]):
                                    account_ids.append(account_id.id)
                            partner_id = amount_rule.partner_id.id  # 合作伙伴ID
                            cashflow_id = amount_rule.cashflow_id.id  # 现金流量
                            product_id = amount_rule.product_id.id  # 产品ID
                            analytic_id = amount_rule.analytic_id.id  # 分析账户
                            if amount_rule.amount_ratio:
                                amount_ratio = amount_rule.amount_ratio  # 取数比例
                            else:
                                amount_ratio = 1
                            amount_range = amount_rule.amount_range  # 取数范围
                            connector = amount_rule.connector  # 连接符
                            # 按条件取数
                            domain = []
                            domain.append(('account_id', 'in', account_ids))
                            if partner_id:
                                domain.append(('partner_id', '=', partner_id))
                            if cashflow_id:
                                domain.append(('cash_flow_item_id', '=', cashflow_id))
                            if product_id:
                                domain.append(('product_id', '=', product_id))
                            # 处理会计期间
                            account_period = self.env['ps.account.period'].browse(res.period_id.id)
                            # 按月处理起始和结束日期
                            date_start = account_period.date_start
                            date_end = account_period.date_end
                            # 按年处理起始和结束日期
                            year_date_start = account_period.fiscalyear_id.date_start
                            year_date_end = account_period.fiscalyear_id.date_end
                            line_amount = 0  # 生成每个凭证行的金额
                            # 根据取数范围进行取数，以下为判断条件
                            if amount_range == 'DebitOccursM':
                                domain.append(('date', '>=', date_start))
                                domain.append(('date', '<=', date_end))
                                move_lines = self.env['account.move.line'].search(domain)
                                for move_line in move_lines:
                                    # 如果设置了分析账户，那么按照分析账户查找数据，否则去掉分析账户条件
                                    if analytic_id:
                                        move_line_analytic_id = move_line.ps_sub_id.analytic_line_ids.account_id.id
                                        if (move_line.move_id.state == 'posted') and (
                                                move_line_analytic_id == analytic_id):
                                            line_amount += move_line.debit
                                    else:
                                        if move_line.move_id.state == 'posted':
                                            line_amount += move_line.debit
                            elif amount_range == 'CreditOccursM':
                                domain.append(('date', '>=', date_start))
                                domain.append(('date', '<=', date_end))
                                move_lines = self.env['account.move.line'].search(domain)
                                for move_line in move_lines:
                                    if analytic_id:
                                        move_line_analytic_id = move_line.ps_sub_id.analytic_line_ids.account_id.id
                                        if (move_line.move_id.state == 'posted') and (
                                                move_line_analytic_id == analytic_id):
                                            line_amount += move_line.credit
                                    else:
                                        if move_line.move_id.state == 'posted':
                                            line_amount += move_line.credit
                            elif amount_range == 'DebitOccursY':
                                domain.append(('date', '>=', year_date_start))
                                domain.append(('date', '<=', year_date_end))
                                move_lines = self.env['account.move.line'].search(domain)
                                for move_line in move_lines:
                                    if analytic_id:
                                        move_line_analytic_id = move_line.ps_sub_id.analytic_line_ids.account_id.id
                                        if (move_line.move_id.state == 'posted') and (
                                                move_line_analytic_id == analytic_id):
                                            line_amount += move_line.debit
                                    else:
                                        if move_line.move_id.state == 'posted':
                                            line_amount += move_line.debit
                            elif amount_range == 'CreditOccursY':
                                domain.append(('date', '>=', year_date_start))
                                domain.append(('date', '<=', year_date_end))
                                move_lines = self.env['account.move.line'].search(domain)
                                for move_line in move_lines:
                                    if analytic_id:
                                        move_line_analytic_id = move_line.ps_sub_id.analytic_line_ids.account_id.id
                                        if (move_line.move_id.state == 'posted') and (
                                                move_line_analytic_id == analytic_id):
                                            line_amount += move_line.credit
                                    else:
                                        if move_line.move_id.state == 'posted':
                                            line_amount += move_line.credit
                            elif amount_range == 'DebitBalance':
                                move_lines = self.env['account.move.line'].search(domain)
                                for move_line in move_lines:
                                    if analytic_id:
                                        move_line_analytic_id = move_line.ps_sub_id.analytic_line_ids.account_id.id
                                        if (move_line.move_id.state == 'posted') and (
                                                move_line_analytic_id == analytic_id):
                                            line_amount += move_line.debit
                                    else:
                                        if move_line.move_id.state == 'posted':
                                            line_amount += move_line.debit
                            elif amount_range == 'CreditBalance':
                                move_lines = self.env['account.move.line'].search(domain)
                                for move_line in move_lines:
                                    if analytic_id:
                                        move_line_analytic_id = move_line.ps_sub_id.analytic_line_ids.account_id.id
                                        if (move_line.move_id.state == 'posted') and (
                                                move_line_analytic_id == analytic_id):
                                            line_amount += move_line.credit
                                    else:
                                        if move_line.move_id.state == 'posted':
                                            line_amount += move_line.credit
                            elif amount_range == 'DifferenceM':
                                domain.append(('date', '>=', date_start))
                                domain.append(('date', '<=', date_end))
                                move_lines = self.env['account.move.line'].search(domain)
                                for move_line in move_lines:
                                    if analytic_id:
                                        move_line_analytic_id = move_line.ps_sub_id.analytic_line_ids.account_id.id
                                        if (move_line.move_id.state == 'posted') and (
                                                move_line_analytic_id == analytic_id):
                                            line_amount += move_line.debit - move_line.credit
                                    else:
                                        if move_line.move_id.state == 'posted':
                                            line_amount += move_line.debit - move_line.credit
                            elif amount_range == 'DifferenceY':
                                domain.append(('date', '>=', year_date_start))
                                domain.append(('date', '<=', year_date_end))
                                move_lines = self.env['account.move.line'].search(domain)
                                for move_line in move_lines:
                                    if analytic_id:
                                        move_line_analytic_id = move_line.ps_sub_id.analytic_line_ids.account_id.id
                                        if (move_line.move_id.state == 'posted') and (
                                                move_line_analytic_id == analytic_id):
                                            line_amount += move_line.debit - move_line.credit
                                    else:
                                        if move_line.move_id.state == 'posted':
                                            line_amount += move_line.debit - move_line.credit
                            # 判断连接符
                            if connector == '+':
                                amount += line_amount * amount_ratio
                            elif connector == '-':
                                amount -= line_amount * amount_ratio
                            else:
                                amount += line_amount * amount_ratio
                            if move_lines:
                                for move_line in move_lines:
                                    quantity += move_line.quantity
                        # 将生成一条凭证分录的数据保存下来
                        new_move_line.update({
                            'quantity': quantity,
                            'name': carry_over_head.name,
                            'account_id': move.account_id.id,
                            'currency_id': move.currency_id.id,
                            'balance_direction': move.balance_direction,
                            'partner_id': move.partner_id.id,
                            'product_id': move.product_id.id,
                            'analytic_id': move.analytic_id.id,
                            'cashflow_id': move.cashflow_id.id,
                            'amount_direction': move.amount_direction,
                            'amount': amount,
                        })
                        if new_move_line:
                            new_lines.update({move.id: new_move_line})
                    for move in carry_over_head.move_ids:
                        if move.take_other_total:  # 取对方科目合计
                            amount = 0
                            for new_line in new_lines:
                                if move.id == new_line:
                                    need_total = new_line
                                else:
                                    amount += new_lines[new_line]['amount']
                            new_lines[need_total]['amount'] = amount
                # 将生成一个move的数据保存到new_move这个字典中，最后将new_move这个字典进行返回
                if new_lines:
                    new_move.update({carry_over_head.id: new_lines})
        return new_move

    @api.multi
    def post(self):
        new_moves = self._get_move_lines()
        for res in self:
            journal_id = res.journal_id.id
            account_period = self.env['ps.account.period'].browse(res.period_id.id)
            date_start = account_period.date_start
            date_end = account_period.date_end
        for new_move in new_moves:
            account_move = self.env['account.move'].search(
                [('carry_over_head_id', '=', new_move), ('date', '>=', date_start), ('date', '<=', date_end)])
            if account_move:
                raise ValidationError(
                    _(
                        'Custom carry-over voucher have been generated,Delete the {} voucher before creating them.').format(account_move.name))
            move = self.env['account.move'].create({
                'ps_create_user': self.env.user.id,
                'journal_id': journal_id,
                'date': date_end,
            })
            move.update({'ref': move.name})
            val = []
            auxiliary = []  # 辅助核算
            for line in new_moves[new_move]:
                amount = 0
                if new_moves[new_move][line]['amount_direction'] == 'plus':
                    amount = abs(new_moves[new_move][line]['amount'])
                elif new_moves[new_move][line]['amount_direction'] == 'negative':
                    amount = -abs(new_moves[new_move][line]['amount'])
                else:
                    amount = new_moves[new_move][line]['amount']
                account = self.env['account.account'].browse(new_moves[new_move][line]['account_id'])
                if account.ps_auxiliary_state == '1':
                    auxiliary.append({
                        'partner_id': new_moves[new_move][line]['partner_id'],
                        'product_id': new_moves[new_move][line]['product_id'],
                        'amount': amount,
                        'quantity': new_moves[new_move][line]['quantity'],
                        'balance_direction': new_moves[new_move][line]['balance_direction'],
                        'analytic_ids': [(0, 0, {
                            'account_id': new_moves[new_move][line]['analytic_id'],
                            'name': new_moves[new_move][line]['name'],
                        })]
                    })
                if new_moves[new_move][line]['balance_direction'] == 'debit':
                    val.append((0, 0, {
                        'name': new_moves[new_move][line]['name'],
                        'product_id': new_moves[new_move][line]['product_id'],
                        'partner_id': new_moves[new_move][line]['partner_id'],
                        'account_id': new_moves[new_move][line]['account_id'],
                        'currency_id': new_moves[new_move][line]['currency_id'],
                        'debit': amount,
                    }))
                elif new_moves[new_move][line]['balance_direction'] == 'credit':
                    val.append((0, 0, {
                        'name': new_moves[new_move][line]['name'],
                        'product_id': new_moves[new_move][line]['product_id'],
                        'partner_id': new_moves[new_move][line]['partner_id'],
                        'account_id': new_moves[new_move][line]['account_id'],
                        'currency_id': new_moves[new_move][line]['currency_id'],
                        'credit': amount,
                    }))
            move.line_ids = val
            # 处理辅助核算项目
            for line in new_moves[new_move]:
                if new_moves[new_move][line]['product_id']:  # 如果设置了产品才进行辅助核算，否则不设置辅助核算
                    for move_line in move.line_ids:
                        if move_line.debit != 0 and move_line.ps_is_sub:
                            for aux in auxiliary:
                                if aux['balance_direction'] == 'debit' and move_line.debit == aux['amount']:
                                    sub_id = self.env['ps.account.move.line.sub'].create({
                                        'ps_consider_partner': aux['partner_id'],
                                        'ps_consider_product': aux['product_id'],
                                        'ps_consider_quantity': aux['quantity'],
                                        'product_uom_id': self.env['product.product'].search(
                                            [('id', '=', aux['product_id'])]).uom_id.id,
                                        'unit_price': abs(amount / aux['quantity'] if aux['quantity'] != 0 else 0),
                                        'amount': amount,
                                        'cash_flow_item_id': new_moves[new_move][line]['cashflow_id'],
                                    })
                                    if aux['analytic_ids'][0][2]['account_id']:
                                        sub_id.analytic_line_ids = aux['analytic_ids']
                                    move_line.ps_sub_id = sub_id.id
                        elif move_line.credit != 0 and move_line.ps_is_sub:
                            for aux in auxiliary:
                                if aux['balance_direction'] == 'credit' and move_line.credit == aux['amount']:
                                    sub_id = self.env['ps.account.move.line.sub'].create({
                                        'ps_consider_partner': aux['partner_id'],
                                        'ps_consider_product': aux['product_id'],
                                        'ps_consider_quantity': aux['quantity'],
                                        'product_uom_id': self.env['product.product'].search(
                                            [('id', '=', aux['product_id'])]).uom_id.id,
                                        'unit_price': abs(amount / aux['quantity'] if aux['quantity'] != 0 else 0),
                                        'amount': amount,
                                        'cash_flow_item_id': new_moves[new_move][line]['cashflow_id'],
                                    })
                                    if aux['analytic_ids'][0][2]['account_id']:
                                        sub_id.analytic_line_ids = aux['analytic_ids']
                                    move_line.ps_sub_id = sub_id.id

            move.carry_over_head_id = new_move  # 将规则的id保存到account.move上的carry_over_head_id字段上
        self.unlink()


# 自定义结转凭证头
class PsAccountCarryOverHead(models.Model):
    _name = "ps.account.carry.over.head"
    _description = "Ps Account Carry Over Head"

    is_generate = fields.Boolean(string='Generate Voucher')  # 是否生成凭证
    carry_over_move_no = fields.Char(string='Number')  # 编号
    name = fields.Char(string='Name')  # 名称
    carry_over_create_id = fields.Many2one('ps.account.carry.over.create', string='Carry Over Create')  # 关联凭证生成向导
    move_ids = fields.One2many('ps.account.carry.over.move', 'head_id', string='Account Carry Over Move')  # 关联凭证行

    _sql_constraints = [
        ('move_no_unique', 'UNIQUE(carry_over_move_no)', 'Number must be unique!'),
    ]


# 自定义结转凭证行
class PsAccountCarryOverMove(models.Model):
    _name = "ps.account.carry.over.move"
    _description = "Ps Account Carry Over Move"

    head_id = fields.Many2one('ps.account.carry.over.head', string='Account Carry Over Head')  # 关联凭证头
    account_id = fields.Many2one('account.account', string='Account ID')  # 关联科目
    balance_direction = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], string='Balance Direction')  # 分录方向
    currency_id = fields.Many2one('res.currency', string='Currency')  # 关联币种
    partner_id = fields.Many2one('res.partner', string='Partner')  # 关联合作伙伴
    product_id = fields.Many2one('product.template', string='Product')  # 关联产品
    cashflow_id = fields.Many2one('ps.cashflow.item', string='Cash Flow Item')  # 现金流量项目
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic ID')  # 分析账户
    amount_direction = fields.Selection([('plus', '+'), ('negative', '-')], string='Amount Direction')  # 金额方向
    rule_amount_ids = fields.One2many('ps.account.carry.over.amount', 'carry_over_move_id',
                                      string='Amount Rule')  # 关联取数规则
    take_other_total = fields.Boolean(string="Take each other's total", default=False)  # 取对方科目合计


# 取数规则
class PsAccountCarryOverAmount(models.Model):
    _name = "ps.account.carry.over.amount"
    _description = "Ps Account Carry Over Amount"

    carry_over_move_id = fields.Many2one('ps.account.carry.over.move', string='Carry Over Move')  # 关联凭证行
    account_substr = fields.Char(string='Account Substr')  # 科目位数
    account_no = fields.Char(string='Account No')  # 科目编号
    currency_id = fields.Many2one('res.currency', string='Currency')  # 币种
    partner_id = fields.Many2one('res.partner', string='Partner')  # 合作伙伴
    product_id = fields.Many2one('product.template', string='Product')  # 产品
    cashflow_id = fields.Many2one('ps.cashflow.item', string='Cash Flow Item')  # 现金流量项目
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic ID')  # 分析账户
    amount_ratio = fields.Float(string='Amount Ratio', default=1)  # 取数比例
    amount_range = fields.Selection([
        ('DebitOccursM', 'DebitOccursM'),  # 借方发生（本期）
        ('CreditOccursM', 'CreditOccursM'),  # 贷方发生（本期）
        ('DebitOccursY', 'DebitOccursY'),  # 借方发生（本年累计）
        ('CreditOccursY', 'CreditOccursY'),  # 贷方发生（本年累计）
        ('DebitBalance', 'DebitBalance'),  # 借方余额
        ('CreditBalance', 'CreditBalance'),  # 贷方余额
        ('DifferenceM', 'DifferenceM'),  # 借贷余额（本期）
        ('DifferenceY', 'DifferenceY'),  # 借贷余额（本年累计）
    ])  # 取数范围
    connector = fields.Selection([('+', '+'), ('-', '-')])  # 连接符


# # 自定义结转凭证记录
# class PsAccountCarryOverLog(models.Model):
#     _name = "ps.account.carry.over.log"
#     _description = "Ps Account Carry Over Log"
#
#     carry_over_id = fields.Many2one('ps.account.carry.over.head', string='Number')  # 编号
#     carry_over_name = fields.Char(string='Carry Over Name')  # 名称
#     company_id = fields.Many2one('res.company', string='Company')  # 公司
#     period_id = fields.Many2one('ps.account.period', string='Account Period')  # 期间
#     move_build = fields.Boolean(string='Move Build', default=False)  # 是否生成凭证
#     move_id = fields.Many2one('account.move', string='Move Number')  # 凭证编号
class AccountMove(models.Model):
    _inherit = 'account.move'

    carry_over_head_id = fields.Many2one('ps.account.carry.over.head', string='Carry Over Head ID')  # 关联规则定义