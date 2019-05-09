# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, exceptions, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.osv.orm import setup_modifiers
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime
from passlib.hash import sha256_crypt
from passlib.context import CryptContext


class ResPartner(models.Model):
    _inherit = "res.partner"

    ps_member_no = fields.Char(string='Member No.', index=True)#会员卡号
    ps_start_date = fields.Datetime(string='Start From')#会员有效日期
    ps_end_date = fields.Datetime(string='Expire On')#会员失效日期
    ps_member_state = fields.Selection([
        ('new', 'Draft'), ('effective', 'Active'), ('expiry', 'Expired'),
        ('loss', 'Loss'), ('logoff', 'Archived')
    ], string='Member Status', default='new', help='Draft:New member, not activated yet;\n'
                'Active: When the effective date reached, the system automatically converts to the "effective" status.\n'
                'Expired: When the expiry date exceeded, the system automatically converts to the "expiry" status.\n'
                'Loss: When card lost or password forgot, not allowed to consume using POS.\n'
                'Archived: Customer archived, member also cancelled, initialize the balance of points and deposit.')
    ps_member_category_id = fields.Many2one('ps.member.category', string='Member Category')#会员状态
    ps_is_use_password = fields.Boolean(string='Use Password', related='ps_member_category_id.is_use_password', readonly=True)#是否使用密码
    ps_is_use_point = fields.Boolean(string='Use Point', related='ps_member_category_id.is_use_point', readonly=True)#是否使用积分
    ps_is_use_deposit = fields.Boolean(string='Use Deposit', related='ps_member_category_id.is_use_deposit', readonly=True)#是否使用储值
    ps_member_password = fields.Char(string='Member Password', compute='_compute_ps_password', inverse='_inverse_ps_password', store=True)#密码
    ps_member_password_encryption = fields.Char(string='Member Password Encryption') #加密密码
    ps_last_consumption_date = fields.Datetime(string='Last Consumption Date')  # 最后一次消费日期

    cashflow_ids = fields.One2many('ps.member.cashflow.account', 'partner_id', string='Cashflow')  # 关联流水账
    #初始
    ps_member_initial_deposit = fields.Float(string='Initial Amount', digits=dp.get_precision('ps_unit_price'))#初始储值
    ps_member_initial_bonus = fields.Float(string='Initial Bonus', digits=dp.get_precision('ps_unit_price'))#初始赠送金额
    ps_member_initial_point = fields.Float(string='Initial Point', digits=dp.get_precision('ps_pos_point'))#初始积分
    ps_member_initial_consumption = fields.Float(string='Initial Consumption', digits=dp.get_precision('ps_unit_price'))# 初始消费
    #余额
    ps_member_balance_deposit = fields.Float(string='Remaining Amount', digits=dp.get_precision('ps_unit_price'),
                                             compute='_get_usage_statistics', store=True)#储值余额
    ps_member_balance_bonus = fields.Float(string='Remaining Bonus', digits=dp.get_precision('ps_unit_price'),
                                           compute='_get_usage_statistics', store=True)#赠送金额的余额
    ps_member_balance_point = fields.Float(string='Remaining Point', digits=dp.get_precision('ps_pos_point'),
                                           compute='_get_usage_statistics', store=True)#积分余额
    #合计
    ps_sum_deposit_amount = fields.Float('Total Deposit Amount', digits=dp.get_precision('ps_unit_price'), compute='_get_usage_statistics') #储值金额合计
    ps_sum_bonus_amount = fields.Float('Total Bonus Amount', digits=dp.get_precision('ps_unit_price'), compute='_get_usage_statistics') #赠送金额合计
    ps_sum_bonus_point = fields.Float('Total Bonus Point', digits=dp.get_precision('ps_pos_point'), compute='_get_usage_statistics') #赠送积分合计
    #消费合计
    ps_sum_consume_deposit_amount = fields.Float('Total Consume Deposit Amount', digits=dp.get_precision('ps_unit_price'), compute='_get_usage_statistics') #消费储值金额合计
    ps_sum_consume_bonus_amount = fields.Float('Total Consume Bonus Amount', digits=dp.get_precision('ps_unit_price'), compute='_get_usage_statistics') #消费赠送金额合计
    ps_sum_consume_bonus_point = fields.Float('Total Consume Bonus Point', digits=dp.get_precision('ps_pos_point'), compute='_get_usage_statistics') #消费积分合计
    ps_sum_consume_cash = fields.Float('Total Consume Cash', digits=dp.get_precision('ps_unit_price'), compute='_get_usage_statistics') #消费现金合计
    #消费信息
    ps_consume_count = fields.Integer('Consume Count', default=0, compute='_get_usage_statistics') #消费次数
    ps_consume_amount = fields.Float('Consume Amount', digits=dp.get_precision('ps_unit_price'), default=0, compute='_get_usage_statistics')  # 消费金额
    _sql_constraints = [
        ('ps_member_no', 'unique(ps_member_no)', _('Membership card number already exists')),
    ]

    @api.constrains('ps_member_password')
    def _check_length_of_ps_password(self):
        for r in self:
            if r.ps_member_password and len(r.ps_member_password) > 6:
                raise ValidationError(_('Please input 6-digit number as password'))
            elif r.ps_member_password and len(r.ps_member_password) <= 5:
                raise ValidationError(_('Please input 6-digit number as password'))
            elif r.ps_member_password and not r.ps_member_password.isdigit():
                raise ValidationError(_('Please input 6-digit number as password'))

    @api.constrains('ps_start_date', 'ps_end_date')
    def _check_start_and_end_date(self):
        for r in self:
            if r.ps_start_date and r.ps_end_date and r.ps_start_date > r.ps_end_date:
                raise ValidationError(_('Start date cannot be later than end date.'))

    @api.constrains('ps_member_category_id','ps_end_date')
    def _check_member_date_and_category_date(self):
        for r in self:
            if r.ps_member_category_id and r.ps_end_date:  # 有类别且有日期(会员日期不能晚于类别日期)
                end_date = self.env['ps.member.category'].search([('id', '=', r.ps_member_category_id.id)])
                if end_date.expiry_date and r.ps_end_date > end_date.expiry_date:
                    raise ValidationError(
                        _('Member end date should not be later than the end date of the category he/she belongs'))

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if res.ps_member_no and not res.ps_member_category_id:
            category_id = self.env['ps.member.category'].search([('is_default_category', '=', True)])
            if category_id:
                res.write({'ps_member_category_id': category_id.id})
                res.write({'ps_end_date': category_id.expiry_date})
                res.write({'ps_member_password': category_id.member_password})
                res.write({'property_product_pricelist': category_id.product_pricelist_id})
        if res.ps_member_no and res.ps_member_category_id:
            res.write({'property_product_pricelist': res.ps_member_category_id.product_pricelist_id})
        return res

    @api.multi
    def write(self, vals):
        if 'ps_member_no' in vals and 'ps_member_category_id' not in vals:  # 有卡号无类别
            category_id = self.env['ps.member.category'].search([('is_default_category', '=', True)])
            if category_id:
                vals['ps_member_category_id'] = category_id.id
                vals['ps_end_date'] = category_id.expiry_date
                vals['ps_member_password'] = category_id.member_password
                vals['property_product_pricelist'] = category_id.product_pricelist_id
        elif 'ps_member_no' in vals and 'ps_member_category_id' in vals and 'ps_end_date' not in vals:  # 有卡号有类别无日期
            category_id = self.env['ps.member.category'].search([('id', '=', vals['ps_member_category_id'])])
            vals['ps_end_date'] = category_id.expiry_date
        elif 'ps_member_no' in vals and 'ps_member_category_id' in vals and 'ps_member_password' not in vals:  # 有卡号有类别无密码
            category_id = self.env['ps.member.category'].search([('id', '=', vals['ps_member_category_id'])])
            vals['ps_member_password'] = category_id.member_password
        res = super(ResPartner, self).write(vals)
        return res

    @api.multi
    @api.depends('cashflow_ids.deposit_amount','cashflow_ids.consume_deposit_amount','cashflow_ids.bonus_amount','cashflow_ids.consume_bonus_amount','cashflow_ids.bonus_point','cashflow_ids.consume_bonus_point','cashflow_ids.consume_cash', 'ps_member_initial_deposit', 'ps_member_initial_bonus', 'ps_member_initial_point', 'ps_member_initial_consumption')
    def _get_usage_statistics(self):
        for order in self:
            if order.cashflow_ids and len(order.cashflow_ids) > 0:
                # 储值金额合计
                order.ps_sum_deposit_amount = 0
                # 赠送金额合计
                order.ps_sum_bonus_amount = 0
                # 赠送积分合计
                order.ps_sum_bonus_point = 0
                # 消费储值金额合计
                order.ps_sum_consume_deposit_amount = 0
                # 消费赠送金额合计
                order.ps_sum_consume_bonus_amount = 0
                # 消费积分合计
                order.ps_sum_consume_bonus_point = 0
                # 消费现金合计
                order.ps_sum_consume_cash = 0
                # 消费次数
                order.ps_consume_count = 0
                for record in order.cashflow_ids:
                    if record.is_reset == False:
                        order.ps_sum_deposit_amount += record.deposit_amount
                        order.ps_sum_bonus_amount += record.bonus_amount
                        order.ps_sum_bonus_point += record.bonus_point
                        order.ps_sum_consume_deposit_amount += record.consume_deposit_amount
                        order.ps_sum_consume_bonus_amount += record.consume_bonus_amount
                        order.ps_sum_consume_bonus_point += record.consume_bonus_point
                        order.ps_sum_consume_cash += record.consume_cash

                    if record.type == 'depositconsume' or record.type == 'cashconsume':
                        order.ps_consume_count = order.ps_consume_count + 1

                # 消费金额
                order.ps_consume_amount = order.ps_member_initial_consumption + order.ps_sum_consume_deposit_amount + order.ps_sum_consume_bonus_amount + order.ps_sum_consume_cash
                # 储值余额
                order.ps_member_balance_deposit =order.ps_member_initial_deposit + order.ps_sum_deposit_amount - order.ps_sum_consume_deposit_amount
                # 赠送金额余额
                order.ps_member_balance_bonus =order.ps_member_initial_bonus + order.ps_sum_bonus_amount - order.ps_sum_consume_bonus_amount
                # 积分余额
                order.ps_member_balance_point =order.ps_member_initial_point + order.ps_sum_bonus_point - order.ps_sum_consume_bonus_point
            elif order.ps_member_initial_deposit or order.ps_member_initial_bonus or order.ps_member_initial_point:
                order.ps_member_balance_deposit = order.ps_member_initial_deposit
                order.ps_member_balance_bonus = order.ps_member_initial_bonus
                order.ps_member_balance_point = order.ps_member_initial_point

    @api.model
    def _ps_activate_member(self, record_ids):#动作-会员生效
        while len(record_ids) > 0:
            id = record_ids.pop(0)
            line = self.env['res.partner'].search([('id', '=', id)])
            if line.ps_member_state in ['new', 'expiry', 'loss']:
                line.write({'ps_member_state': 'effective'})
            else:
                raise ValidationError(_('Only members in "Draft","Expired" and "Loss" state are allowed to be activated'))
        return

    @api.model
    def _ps_deactivate_member(self, record_ids):#动作-会员失效
        while len(record_ids) > 0:
            id = record_ids.pop(0)
            line = self.env['res.partner'].search([('id', '=', id)])
            if line.ps_member_state == 'effective':
                line.write({'ps_member_state': 'expiry'})
            else:
                raise ValidationError(_('Only members in "Active" state are allowed to be deactivated'))
        return

    @api.model
    def _ps_report_loss_member(self, record_ids):#动作-会员挂失
        while len(record_ids) > 0:
            id = record_ids.pop(0)
            line = self.env['res.partner'].search([('id', '=', id)])
            if line.ps_member_state == 'effective':
                line.write({'ps_member_state': 'loss'})
            else:
                raise ValidationError(_('Only members in "Active" state are allowed to report the loss'))
        return

    @api.model
    def _automatically_update_member_state(self):#会员自动生效与失效，仅适用会员状态处于'草稿'和'生效'状态的会员
        record_sets = self.env['res.partner'].search([('customer', '=', True)])
        today_now = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        for line in record_sets:
            if line.ps_start_date and line.ps_start_date <= today_now and \
            line.ps_member_state == 'new': #已设置生效日期，生效日期早于当前日期，且会员状态为'草稿'
                line.write({'ps_member_state': 'effective'})
            if line.ps_end_date and line.ps_end_date <= today_now and \
            line.ps_member_state == 'effective': #设置失效日期，失效日期早于当前日期，且会员状态为'生效'
                line.write({'ps_member_state': 'expiry'})
        return


    def _compute_ps_password(self):
        self.env.cr.execute('SELECT id, ps_member_password FROM res_partner WHERE id IN %s', [tuple(self.ids)])
        password_dict = dict(self.env.cr.fetchall())
        for partner in self:
            partner.ps_member_password = password_dict[partner.id]

    @api.depends('ps_member_password')
    def _inverse_ps_password(self):
        for partner in self:
            partner._set_ps_password(partner.ps_member_password)
            self.invalidate_cache()

    def _set_ps_password(self, password):
        if password:
            self.ensure_one()
            """ Encrypts then stores the provided plaintext password for the user
            ``self``
            """
            encrypted = sha256_crypt.encrypt(password)
            self._set_ps_encrypted_password(encrypted)

    def _set_ps_encrypted_password(self, encrypted):
        """ Store the provided encrypted password to the database, and clears
        any plaintext password, '666666' is only used for display in frontend
        and can be changed freely (but 6 digit number string recommended here) .
        """
        self.env.cr.execute(
            "UPDATE res_partner SET ps_member_password='666666', ps_member_password_encryption=%s WHERE id=%s",
            (encrypted, self.id))

    @api.onchange('ps_member_category_id')
    def _onchange_member_category_id(self):
        if self.property_product_pricelist:
            self.property_product_pricelist = self.ps_member_category_id.product_pricelist_id
            return {
                'warning': {
                    'title': _('Check Pricelist'),
                    'message': _("The customer's price list has been updated to the member category's price list."),
                }
            }
        self.property_product_pricelist = self.ps_member_category_id.product_pricelist_id
        if self.ps_member_category_id.is_use_password:
            self.ps_member_password = self.ps_member_category_id.member_password

    @api.model
    def get_member_pass_boolean(self, ps_member_no):
        if self.search([('ps_member_no', '=', ps_member_no)]).ps_member_password_encryption:
            return True
        else:
            return False

    @api.model
    def verify_member_password(self, ps_member_no, pw):
        encrypted_pass = self.search([('ps_member_no', '=', ps_member_no)]).ps_member_password_encryption
        if sha256_crypt.verify(pw, encrypted_pass):
            return 'pass'
        else:
            return ''





