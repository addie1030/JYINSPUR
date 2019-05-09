# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, tools, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.addons import decimal_precision as dp
import logging
from odoo.tools.safe_eval import safe_eval
from datetime import datetime

_logger = logging.getLogger(__name__)


class PsMemberCategory(models.Model):
    _name = 'ps.member.category'
    _description = 'Ps Member Category'
    _sql_constraints = [('code_unique', 'unique(code,company_id)', _('Member category code cannot be repeated'))]

    code = fields.Char(string='Category Code', copy=False,
                       default=lambda self: _('New'))  # 会员类别编号
    name = fields.Char(string='Category Name')  # 会员类别名称
    expiry_date = fields.Datetime(string='Term of validity')  # 有效期
    status = fields.Selection([('active', 'Active'), ('archived', 'Archived')], string='Status')  # 状态
    company_id = fields.Many2one('res.company', string='Company')  # 公司
    is_use_password = fields.Boolean(string='Use Password', default=False)  # 是否需要密码
    member_password = fields.Char(string='Password')  # 会员密码
    is_use_deposit = fields.Boolean(string='Use Deposit')  # 储值
    is_use_point = fields.Boolean(string='Use Point')  # 积分
    is_default_category = fields.Boolean(string='Default Category')  # 默认会员类别
    property_account_deposit_id = fields.Many2one('account.account', string='Deposit Account',
                                                  domain=[('deprecated', '=', False)],
                                                  company_dependent=True)  # 储值科目
    property_account_present_id = fields.Many2one('account.account', string='Donation Amount Account',
                                                  domain=[('deprecated', '=', False)],
                                                  company_dependent=True)  # 赠送金额科目
    general_expense = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Consumption')  # 消费
    general_point = fields.Float(digits=dp.get_precision('ps_pos_point'), string='Point')  # 积分
    member_gift_set_ids = fields.One2many('ps.member.category.gift.rule', 'member_category_id',
                                          string='Store Formula')  # 赠送公式
    member_gift_amount_use_ids = fields.One2many('ps.member.category.bonus.use.set', 'member_category_id',
                                                 string='Use Formula')  # 使用公式

    item_ids = fields.One2many('ps.member.category.point.rule', 'member_category_id')
    product_pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')

    @api.model
    def create(self, vals):
        if 'code' not in vals or vals['code'] == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('ps.member.category') or _('New')
        return super(PsMemberCategory, self).create(vals)

    @api.constrains('is_default_category')
    def _check_default_category(self):
        for r in self:
            if r.is_default_category:
                recs = self.search([('id', '!=', r.id)])
                if recs:
                    recs.write({'is_default_category': False})

    @api.multi
    def unlink(self):
        for r in self:
            if self.env['res.partner'].search([('ps_member_category_id', '=', r.id)]):
                raise ValidationError(_('Member category ') + r.name + _(' is using, can not delete.'))
        return super(PsMemberCategory, self).unlink()

    @api.constrains('member_password')
    def _check_length_of_ps_password(self):
        for r in self:
            if r.member_password and len(r.member_password) > 6:
                raise ValidationError(_('Please input 6-digit number as password'))
            elif r.member_password and len(r.member_password) <= 5:
                raise ValidationError(_('Please input 6-digit number as password'))
            elif r.member_password and not r.member_password.isdigit():
                raise ValidationError(_('Please input 6-digit number as password'))

class PsMemberCategoryGiftRule(models.Model):
    _name = 'ps.member.category.gift.rule'
    _description = 'ps.member.category.gift.rule'

    member_category_id = fields.Many2one('ps.member.category', string='Member Category', ondelete='cascade')  # 会员类别
    date_begin = fields.Datetime(string='Begin Date')  # 开始日期
    date_end = fields.Datetime(string='End Date')  # 结束日期
    min_deposit = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Min deposit Amount')  # 最小储值金额
    give_way = fields.Selection([('percentage', 'Percentage'), ('formula', 'Formula')], string='Gift Method')  # 赠送方式
    percent_amount = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Percent Amount')  # 赠送金额（比例）
    formula_percent_amount = fields.Char(string='Percent Amount Formula', compute='_set_formula_percent_amount',
                                         store=True)  # 赠送金额（比例）公式
    percent_point = fields.Float(digits=dp.get_precision('ps_pos_point'), string='Percent Point')  # 赠送积分（比例）
    formula_percent_point = fields.Char(string='Percent Point Formula', compute='_set_formula_percent_point',
                                        store=True)  # 赠送积分（比例）公式
    formula_deposit = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Formula deposit')  # 储值金额（公式）
    formula_amount = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Formula Amount')  # 赠送金额（公式）
    formula_point = fields.Float(digits=dp.get_precision('ps_pos_point'), string='Formula Point')  # 赠送积分（公式）
    gift_formula = fields.Char(string='Gift Formula', compute='_compute_deposit_formula', store=True)  # 赠送公式
    sequence = fields.Integer(string='Sequence', default=16)

    @api.constrains('date_begin', 'date_end')
    def _check_date_begin_date_end(self):
        for r in self:
            if r.date_begin and r.date_end and r.date_begin > r.date_end:
                raise ValidationError(_('Start date cannot be later than end date.'))

    @api.one
    @api.depends('give_way', 'percent_amount')
    def _set_formula_percent_amount(self):
        if self.percent_amount:
            self.formula_percent_amount = 'x * %s / 100' % str(self.percent_amount)

    @api.one
    @api.depends('give_way', 'percent_point')
    def _set_formula_percent_point(self):
        if self.percent_point:
            self.formula_percent_point = 'x * %s / 100' % str(self.percent_point)

    @api.multi
    @api.depends('give_way', 'percent_amount', 'percent_point', 'formula_deposit', 'formula_amount', 'formula_point')
    def _compute_deposit_formula(self):
        str_formula = ''
        for r in self:
            if r.give_way == 'percentage':
                if r.percent_amount and r.percent_point:
                    str_formula = _('Bonus amount ') + str(r.percent_amount) + '%' + ' & ' + _(
                        'Bonus points ') + str(
                        r.percent_point) + '%'
                elif r.percent_amount:
                    str_formula = _('Bonus amount ') + str(r.percent_amount) + '%'
                elif r.percent_point:
                    str_formula = _('Bonus points ') + str(r.percent_point) + '%'
                # self.update({'gift_formula': str_formula})
                r.gift_formula = str_formula
            elif r.give_way == 'formula':
                str_deposit = _('Store amount') + str(r.formula_deposit) if r.formula_deposit else ''
                str_amount = _(' Bonus amount') + str(r.formula_amount) if r.formula_amount else ''
                str_point = _(' Bonus points') + str(r.formula_point) if r.formula_point else ''
                str_formula_2 = str_deposit + str_amount + str_point
                # self.update({'gift_formula': str_formula_2})
                r.gift_formula = str_formula_2

    def get_bonus_amount_points_by_date(self, category_id, date, storeamount):
        bonus_amount = 0.00
        bonus_point = 0.00
        rec = self.search([('date_begin', '<=', date),
                           ('date_end', '>=', date),
                           ('member_category_id', '=', category_id),
                           ('min_deposit', '<=', storeamount)], order='sequence', limit=1)
        if rec:
            if rec.give_way == 'percentage':  # 按比例赠送
                if rec.formula_percent_amount:
                    bonus_amount = safe_eval(rec.formula_percent_amount, {'x': storeamount})
                if rec.formula_percent_point:
                    bonus_point = safe_eval(rec.formula_percent_point, {'x': storeamount})
            if rec.give_way == 'formula':
                if storeamount >= rec.formula_deposit:
                    bonus_amount = rec.formula_amount
                    bonus_point = rec.formula_point
            return bonus_amount, bonus_point

        rec = self.search([('date_begin', '<=', date),
                           ('date_end', '>=', date),
                           ('member_category_id', '=', category_id),
                           ('min_deposit', '<=', storeamount),
                           ('formula_deposit', '<=', storeamount)], order='sequence', limit=1)
        if rec:
            if rec.formula_amount:
                bonus_amount = rec.formula_amount
            if rec.formula_point:
                bonus_point = rec.formula_point
        return bonus_amount, bonus_point

    def get_bonus_amount_points_by_amount(self, category_id, storeamount):
        bonus_amount = 0.00
        bonus_point = 0.00
        rec = self.search([('min_deposit', '<=', storeamount),
                           ('member_category_id', '=', category_id),
                           ('date_begin', '=', None),
                           ('date_end', '=', None)], order='sequence', limit=1)
        if rec:
            if rec.give_way == 'percentage':  # 按比例赠送
                if rec.formula_percent_amount:
                    bonus_amount = safe_eval(rec.formula_percent_amount, {'x': storeamount})
                if rec.formula_percent_point:
                    bonus_point = safe_eval(rec.formula_percent_point, {'x': storeamount})
            if rec.give_way == 'formula':
                if storeamount >= rec.formula_deposit:
                    bonus_amount = rec.formula_amount
                    bonus_point = rec.formula_point
            return bonus_amount, bonus_point

        rec = self.search([('formula_deposit', '<=', storeamount),
                           ('min_deposit', '<=', storeamount),
                           ('date_begin', '=', None),
                           ('date_end', '=', None),
                           ('member_category_id', '=', category_id)], order='sequence', limit=1)
        if rec:
            if rec.formula_amount:
                bonus_amount = rec.formula_amount
            if rec.formula_point:
                bonus_point = rec.formula_point
        return bonus_amount, bonus_point

    def get_bonus_amount_points(self, category_id, date, storeamount):
        bonus_amount = 0.00
        bonus_point = 0.00

        pmc = self.env['ps.member.category'].browse(category_id)

        if pmc.expiry_date:
            s_date = pmc.expiry_date.strftime("%Y-%m-%d")
            expiry_date = datetime.strptime(s_date, '%Y-%m-%d').date()

        if pmc.expiry_date and expiry_date < date:
            return bonus_amount, bonus_point

        bonus_amount, bonus_point = self.get_bonus_amount_points_by_date(category_id, date, storeamount)
        if bonus_amount or bonus_point:
            return bonus_amount, bonus_point

        return self.get_bonus_amount_points_by_amount(category_id, storeamount)


class PsMemberCategoryBonusUseSet(models.Model):
    _name = 'ps.member.category.bonus.use.set'
    _description = 'ps.member.category.bonus.use.set'

    member_category_id = fields.Many2one('ps.member.category', string='Member Category', ondelete='cascade')  # 会员类别
    date_begin = fields.Datetime(string='Begin Date')  # 开始日期
    date_end = fields.Datetime(string='End Date')  # 结束日期
    min_consumption = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Min Consumption')  # 最低消费
    consumption_method = fields.Selection([('present', 'Present'),
                                           ('percentage', 'Percentage'),
                                           ('formula', 'Formula')], string='Consumption Method')  # 消费方式
    percentage_deposit = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Percentage Deposit')  # 储值金额(比例)
    formula_percentage_deposit = fields.Char(string='Percentage Deposit Formula',
                                             compute='_set_formula_percentage_deposit', store=True)  # 储值金额使用公式
    percentage_bonus = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Percentage Bonus')  # 赠送金额(比例)
    formula_percentage_present = fields.Char(string='Percentage Present Formula',
                                             compute='_set_formula_percentage_present', store=True)  # 赠送金额使用公式
    formula_deposit = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Formula Deposit')  # 储值金额(公式)
    formula_present = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Formula Present')  # 赠送金额(公式)
    formula_deposit_present = fields.Char(string='Deposit Present Formula',
                                          compute='_formula_deposit_present')  # 满额使用公式
    use_formula = fields.Char(string='Use Formula', compute='_set_use_formula', store=True)  # 使用公式
    sequence = fields.Integer(string='Sequence', default=16)

    @api.constrains('date_begin', 'date_end')
    def _check_date_begin_date_end(self):
        for r in self:
            if r.date_begin and r.date_end and r.date_begin > r.date_end:
                raise ValidationError(_('Start date cannot be later than end date.'))

    @api.one
    @api.depends('consumption_method', 'percentage_deposit')
    def _set_formula_percentage_deposit(self):
        if self.consumption_method == 'percentage':
            if self.percentage_deposit:
                self.formula_percentage_deposit = 'consumption * %s / 100' % str(self.percentage_deposit)

    @api.one
    @api.depends('consumption_method', 'percentage_bonus')
    def _set_formula_percentage_present(self):
        if self.consumption_method == 'percentage':
            if self.percentage_bonus:
                self.formula_percentage_present = 'consumption * %s / 100' % str(self.percentage_bonus)

    @api.one
    @api.depends('min_consumption', 'consumption_method', 'formula_deposit', 'formula_present')
    def _formula_deposit_present(self):
        if self.consumption_method == 'formula':
            if self.formula_deposit:
                if self.formula_present:
                    self.formula_deposit_present = 'int(consumption / %s) * %s' % (
                    str(self.formula_deposit), str(self.formula_present))

    @api.multi
    @api.depends('consumption_method', 'percentage_deposit', 'percentage_bonus', 'formula_deposit', 'formula_present')
    def _set_use_formula(self):
        for r in self:
            if r.consumption_method == 'present':
                r.use_formula = _('Use bonus first.')
            elif r.consumption_method == 'percentage':
                str_percentage_deposit = _('Percentage Deposit ') + str(r.percentage_deposit) + '%'
                str_percentage_present = _(' Percentage Bonus ') + str(r.percentage_bonus) + '%'
                r.use_formula = str_percentage_deposit + str_percentage_present
            elif r.consumption_method == 'formula':
                if r.formula_deposit and r.formula_deposit:
                    str_formula_deposit = _('For each ') + str(r.formula_deposit) + _(' consumption,')
                    str_formula_present = str(r.formula_present) + _(' will be decucted in bonus as discount.')
                    r.use_formula = str_formula_deposit + str_formula_present


    @api.constrains('percentage_deposit', 'percentage_bonus', 'formula_deposit', 'formula_present')
    def _check_consumption_method(self):
        for r in self:
            if r.consumption_method == 'percentage':
                if r.percentage_deposit <= 0 or r.percentage_bonus <= 0:
                    raise ValidationError(_('Percentage Deposit and Percentage Bonus can not be empty'))
                if (r.percentage_deposit + r.percentage_bonus) != 100:
                    raise ValidationError(_('The sum of Percentage Deposit and Percentage Bonus must be 100.'))
            elif r.consumption_method == 'formula':
                if r.formula_deposit <= 0 or r.formula_present <= 0:
                    raise ValidationError(_('Formula Deposit and Formula Present can not be empty'))

    def get_bonus_amount_update_member_bonus_info(self, member_id, date, consumption):
        """
        :param member_id: 会员ID
        :param date: 业务日期
        :param consumption: 消费金额
        :return: 扣除的储值金额、赠送金额

        """
        partner_id = self.env['res.partner'].browse(member_id)
        ps_member_balance_bonus = partner_id.ps_member_balance_bonus#会员当前的赠送金额余额

        pmc = self.env['ps.member.category'].browse(partner_id.ps_member_category_id.id)

        if pmc.expiry_date and expiry_date < date:
            raise ValidationError(_('Member category has expired, please pay in cash.'))#会员类别有效期已到，请付现金

        if consumption > partner_id.ps_member_balance_deposit:
            raise ValidationError(_('Insufficient amount of stored value, please pay in cash.'))#储值余额不足，请付现金

        ##先搜有效时间范围内的规则
        rec = self.search([('date_begin', '<=', date),
                           ('date_end', '>=', date),
                           ('member_category_id', '=', partner_id.ps_member_category_id.id),
                           ('min_consumption', '<=', consumption)], order='sequence', limit=1)
        if not rec:##如果找不到，不考虑有效时间
            rec = self.search([('member_category_id', '=', partner_id.ps_member_category_id.id),
                               ('date_begin', '=', None),
                               ('date_end', '=', None),
                               ('min_consumption', '<=', consumption)], order='sequence', limit=1)

        if not rec:
            return consumption, 0

        if rec.consumption_method == 'present':#优先扣除赠送金额
            if consumption > ps_member_balance_bonus:#如果消费金额大于赠送金额余额
                return consumption - ps_member_balance_bonus, ps_member_balance_bonus
            else:
                return 0, consumption
        if rec.consumption_method == 'percentage':#按比例扣除赠送金额
            bonus_amoun = safe_eval(rec.formula_percentage_present, {'consumption': consumption})#按比例需要赠送的金额
        elif rec.consumption_method == 'formula':
            bonus_amoun = safe_eval(rec.formula_deposit_present, {'consumption': consumption})  # 按公式需要赠送的金额
        if bonus_amoun > ps_member_balance_bonus:
            return consumption - ps_member_balance_bonus, ps_member_balance_bonus
        else:
            return consumption - bonus_amoun, bonus_amoun


class PsMemberCategoryPointRule(models.Model):
    _name = 'ps.member.category.point.rule'
    _description = 'Ps Member Category Point Rule'
    _order = "sequence asc, applied_on, categ_id desc, id"

    member_category_id = fields.Many2one('ps.member.category', index=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', ondelete='cascade')
    product_template_id = fields.Many2one('product.template', 'Product Template', ondelete='cascade')
    categ_id = fields.Many2one('product.category', 'Product Category', ondelete='cascade')
    expense = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Amount per consumption')  # 每消费金额
    point = fields.Float(digits=dp.get_precision('ps_pos_point'), string='Give away points')  # 赠送积分
    multiple = fields.Float(digits=dp.get_precision('ps_pos_multiple'), string='Point multiple')  # 积分倍数
    date_start = fields.Datetime('Start Date', required=True)
    date_end = fields.Datetime('End Date', required=True)
    formula_point = fields.Char('Formula Point', compute='_get_formula_point')  # 赠送积分（公式）
    sequence = fields.Integer(default=16)
    applied_on = fields.Selection([
        ('3_global', 'Global'),
        ('2_product_category', ' Product Category'),
        ('1_product', 'Product'),
        ('0_product_variant', 'Product Variant')], "Apply On",
        default='3_global', required=True)
    name = fields.Char('Name', compute='_get_ps_member_category_item_name_price')
    total_point = fields.Char('total_point', compute='_get_ps_member_category_item_name_price')

    @api.one
    @api.depends('categ_id', 'product_template_id', 'product_id', 'member_category_id', 'point', 'multiple')
    def _get_ps_member_category_item_name_price(self):
        if self.categ_id:
            self.name = _("Category: %s") % (self.categ_id.name)
        elif self.product_template_id:
            self.name = self.product_template_id.name
        elif self.product_id:
            self.name = self.product_id.display_name.replace('[%s]' % self.product_id.code, '')
        else:
            self.name = _("All Products")

        if self.multiple:
            self.total_point = _("%s points and %s times") % (self.point, self.multiple)
        else:
            self.total_point = _("%s points") % (self.point)

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        if self.applied_on != '0_product':
            self.product_template_id = False
        if self.applied_on != '1_product_category':
            self.categ_id = False

    @api.onchange('multiple')
    def _onchange_multiple(self):
        if not self.multiple > 0:
            self.multiple = False

    @api.one
    @api.depends('member_category_id', 'expense', 'point', 'multiple')
    def _get_formula_point(self):
        if self.multiple == 0.0:
            self.formula_point = 'x // %s * %s' % (str(self.expense), str(self.point))
        else:
            self.formula_point = 'x // %s * %s * %s' % (str(self.expense), str(self.point), str(self.multiple))

#会员流水账:会员储值单-确认时更新；POS订单-验证时更新；POS订单撤销-验证时更新
class PsMemberCashflowAccount(models.Model):
    _name = 'ps.member.cashflow.account'
    _description = 'ps.member.cashflow.account'

    business_date = fields.Datetime(string='Business Date', required=True) #业务日期
    origin = fields.Reference(string='Source Document', selection=[('account.payment', 'Member deposit'),
                                         ('pos.order', 'POS order')])  # 源单据（会员储值单或者POS订单）
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id) #公司
    user_id = fields.Many2one('res.users', string='Operator', default=lambda self: self._uid) #操作员
    partner_id = fields.Many2one('res.partner', string='Member', required=True) #会员id
    # member_no = fields.Char(string='Member No', related='partner_id.ps_member_no') #会员编号
    # member_name = fields.Char(string='Member Name', related='partner_id.name') #会员名称（客户名）
    is_reset = fields.Boolean(default=False)
    type = fields.Selection([
        ('deposit', 'Deposit value'),
        ('depositconsume', 'Deposit consume'),
        ('cashconsume', 'Cash consume'),
        ('depositrefund', 'Deposit refund'),
        ('cashrefund', 'Cash refund'),
    ], string="Operation Type", default='deposit') #操作类型:储值，消费储值，消费现金，储值退款，现金退款
    deposit_amount = fields.Float('Deposit Amount', digits=dp.get_precision('ps_unit_price')) #储值金额
    consume_deposit_amount = fields.Float('Consume Deposit Amount', digits=dp.get_precision('ps_unit_price')) #消费储值金额
    bonus_amount = fields.Float('Bonus Amount', digits=dp.get_precision('ps_unit_price')) #赠送金额
    consume_bonus_amount = fields.Float('Consume Bonus Amount', digits=dp.get_precision('ps_unit_price')) #消费赠送金额
    bonus_point = fields.Float('Bonus Point', digits=dp.get_precision('ps_pos_point')) #赠送积分
    consume_bonus_point = fields.Float('Consume Bonus Point', digits=dp.get_precision('ps_pos_point')) #消费积分
    consume_cash = fields.Float('Consume Cash', digits=dp.get_precision('ps_unit_price')) #消费现金

