from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    ps_deposit_value_balance = fields.Float('Deposit value balance', compute='_compute_value_balance',
                                            readonly=True,
                                            digits=dp.get_precision('ps_unit_price'))  # 储值余额
    ps_present_bonus = fields.Float('Recharge Bonus', compute="_compute_present",
                                    digits=dp.get_precision('ps_unit_price'))  # 赠送金额
    ps_present_point = fields.Float('Present Point', compute="_compute_present",
                                    digits=dp.get_precision('ps_pos_point'))  # 赠送积分

    @api.constrains('amount')
    def check_amount(self):
        if self.env.context.get('member_deposit'):
            if self.amount <= 0:
                raise ValidationError(_('Deposit amount needs to be greater than 0!'))

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.env.context.get('member_deposit_refund'):
            self.partner_type = 'customer'

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        # Set partner_id domain
        if self.env.context.get('member_deposit') or self.env.context.get('member_deposit_refund'):
            if self.partner_type:
                return {'domain': {'partner_id': [(self.partner_type, '=', True),
                                                  ('ps_member_state', '=', 'effective'),
                                                  ('ps_member_no', '!=', False),
                                                  ('ps_member_category_id.is_use_deposit', '=' , True)]}}
        else:
            return {'domain': {'partner_id': [(self.partner_type, '=', True)]}}


    @api.depends('amount')
    def _compute_value_balance(self):
        self.ps_deposit_value_balance = self.partner_id.ps_member_balance_deposit

    @api.onchange('amount')
    def _compute_present(self):
        category_id = self.partner_id.ps_member_category_id.id
        if category_id:
            date = self.payment_date
            storeamount = self.amount
            self.ps_present_bonus, self.ps_present_point = self.env[
                'ps.member.category.gift.rule'].get_bonus_amount_points(category_id, date, storeamount)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.env.context.get('member_deposit_refund'):
            if self.partner_id:
                self.amount = self.partner_id.ps_member_balance_deposit

    @api.multi
    def post(self):
        result = super(AccountPayment, self).post()
        self.update({'state': 'draft'})
        if not self.env.context.get('member_deposit', False) and not self.env.context.get('member_deposit_refund', False):
            self.update({'state': 'posted'})
            return result
        if not self.env.user.company_id.ps_property_account_sales_discount_id:
            raise ValidationError(_("Please go to the company interface maintenance Consumption Discount Account!"))
        # 将数据写入中间表

        type = 'deposit'
        if self.env.context.get('member_deposit_refund', False):
            type = 'depositrefund'
            operate = 'member_deposit_refund'
            for rec in self:
                self.env['ps.member.cashflow.account'].create({
                    'business_date': rec.create_date,
                    'origin': 'account.payment,' + str(rec.id),
                    'company_id': self.env.user.company_id.id,
                    'user_id': self.env.user.id,
                    'partner_id': rec.partner_id.id,
                    'type': type,
                    'deposit_amount': -rec.ps_deposit_value_balance,  # 储值金额余额
                    'bonus_amount': -rec.partner_id.ps_member_balance_bonus,  # 赠送金额余额
                    'bonus_point': -rec.partner_id.ps_member_balance_point,  # 赠送积分余额
                })
        if self.env.context.get('member_deposit', False):
            type = 'deposit'
            operate = 'member_deposit'
            for rec in self:
                self.env['ps.member.cashflow.account'].create({
                    'business_date': rec.create_date,
                    'origin': 'account.payment,' + str(rec.id),
                    'company_id': self.env.user.company_id.id,
                    'user_id': self.env.user.id,
                    'partner_id': rec.partner_id.id,
                    'type': type,
                    'deposit_amount': rec.amount,  # 储值金额
                    'bonus_amount': rec.ps_present_bonus,  # 赠送金额
                    'bonus_point': rec.ps_present_point,  # 赠送积分
                })
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        move_id = self.env['account.move'].search([('name', '=', self.move_name)]).id  # move_id

        if self.env.context.get('member_deposit', False):
            debit, credit, amount_currency, currency_id = aml_obj.with_context(
                date=self.payment_date)._compute_amount_fields(self.ps_present_bonus, self.currency_id, self.company_id.currency_id)

        if self.env.context.get('member_deposit_refund', False):
            credit, debit, amount_currency, currency_id = aml_obj.with_context(
                date=self.payment_date)._compute_amount_fields(self.ps_present_bonus, self.currency_id, self.company_id.currency_id)

        # 生成贷方凭证分录
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move_id, False)
        counterpart_aml_dict.update(self.with_context({'counterpart_aml': True, 'operate': operate})._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        # 生成借方凭证分录
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move_id, False)
            liquidity_aml_dict.update(self.with_context({'liquidity_aml': True, 'operate': operate})._get_liquidity_move_line_vals(-self.ps_present_bonus))
            aml_obj.create(liquidity_aml_dict)

        #会员信息中的储值余额和赠送余额更新为0
        if self.env.context.get('member_deposit_refund', False):
            # 储值记录先置为失效
            cashflow_ids = self.env['ps.member.cashflow.account'].search([('partner_id', '=', self.partner_id.id)])
            for r in cashflow_ids:
                if r:
                    r.is_reset = True
            # 然后更新为零
            self.partner_id.write({
                'ps_member_balance_deposit': 0,
                'ps_member_balance_bonus': 0,
                'ps_member_initial_deposit': 0,
                'ps_member_initial_bonus': 0,
                'ps_member_initial_point': 0,
                'ps_member_initial_consumption': 0,
                'ps_member_state': 'expiry'
            })
        self.update({'state': 'posted'})
        return result

    # create debit
    def _get_counterpart_move_line_vals(self, invoice=False):
        result = super(AccountPayment, self)._get_counterpart_move_line_vals(invoice=invoice)
        if self.env.context.get('member_deposit', False) or self.env.context.get('member_deposit', False):
            result['account_id'] = self.journal_id.default_credit_account_id.id                             #日记账项贷方
            if self.env.context.get('counterpart_aml', False) :
                result['account_id'] = self.partner_id.ps_member_category_id.property_account_present_id.id #赠送金额
        # if self.env.context.get('member_deposit_refund', False):
        #     result['account_id'] = self.journal_id.default_credit_account_id.id                               #日记账项贷方
        # if self.env.context.get('counterpart_aml', False) and self.env.context.get('operate', '') == 'member_deposit_refund':
        #     result['account_id'] = self.env.user.company_id.ps_property_account_sales_discount_id.id    #公司-消费折扣
        return result

    # create credit
    def _get_liquidity_move_line_vals(self, amount):
        vals = super(AccountPayment, self)._get_liquidity_move_line_vals(amount=amount)
        if self.env.context.get('member_deposit', False) or self.env.context.get('member_deposit', False):
            vals['account_id'] = self.partner_id.ps_member_category_id.property_account_deposit_id.id       #储值科目
            if self.env.context.get('liquidity_aml', False):
                vals['account_id'] = self.env.user.company_id.ps_property_account_sales_discount_id.id      #公司-消费折扣
        # if self.env.context.get('member_deposit_refund', False):
        #     vals['account_id'] = self.partner_id.ps_member_category_id.property_account_deposit_id.id     #储值科目
        # if self.env.context.get('liquidity_aml', False) and self.env.context.get('operate', '') == 'member_deposit_refund':
        #     vals['account_id'] = self.partner_id.ps_member_category_id.property_account_present_id.id   #赠送金额
        return vals

    @api.multi
    def write(self, vals):
        if self.env.context.get('member_deposit_refund', False):
            if vals.get('amount'):
                if round(float(vals['amount']),2) != round(float(self.ps_deposit_value_balance),2):
                    raise ValidationError(_("Partial refund is not allowed, please check!"))
        return super(AccountPayment, self).write(vals)

    @api.model
    def create(self, vals):
        if self.env.context.get('member_deposit_refund', False):
            if round(float(vals['amount']),2) != round(float(self.env['res.partner'].search([('id', '=', vals['partner_id'])]).ps_member_balance_deposit),2):
                raise ValidationError(_("Partial refund is not allowed, please check!"))
        return super(AccountPayment, self).create(vals)