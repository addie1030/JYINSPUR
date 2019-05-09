# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

############################################
# describe：1、修改Odoo的Journal对象，增加凭证字、凭证类型、限制类型、限制科目四个字段
#           2、将在debug模式下才显示的“允许取消记账”，“在工作台上显示”两个参数放到正常模式里
#           3、模块初次安装时，初始化account_Journal表中已有记录的新增加列的值（根据type类型）
# date：20180416
# author：sunny
############################################

class AccountJournal(models.Model):
    _name = 'account.journal'
    _inherit = 'account.journal'


    # sunny modify fields's tip
    update_posted = fields.Boolean(string='Allow cancelling posting',
                                   help="Check this box to allow you to cancel the positng of the voucher under this account type.")
    show_on_dashboard = fields.Boolean(string='Display on the workbench', help="When checked, this account type will be displayed on the workbench.", default=True)
    color = fields.Integer("Color Index", default=0)

    # sunny add four new fields to account_journal table
    ps_voucher_word = fields.Char(string='Voucher Character', required=True, default=lambda self: _('Rem.'))
    ps_voucher_name = fields.Char(string='Voucher Type', required=True, default=lambda self: _('Posting Voucher'))
    ps_control_style = fields.Selection([('0', 'No Control'), ('1', 'Debit Must Have'), ('2', 'Credit Must Have'), ('3', 'No Debit'),
                                         ('4', 'No Credit'), ('5', 'No Voucher'), ('6', 'Voucher Must Have')],
                     string='Restriction Type',default='0', required=True)

    ps_control_account_ids = fields.Many2many('account.account', 'account_account_journal_rel', 'journal_id',
                                              'account_id',
                                              string="Restriction Account",
                                              domain=[('deprecated', '=', False)])


    # @api.model_cr
    # def init(self):
    #     res = super(AccountJournal, self).init()
    #     self.search([('ps_voucher_word', '=', None), ( 'type', '!=', 'cash'), ('type','!=','bank')]).write({'ps_voucher_word': '记', 'ps_voucher_name': '记账凭证'})
    #     self.search([('ps_voucher_word', '=', None), ( 'type', '=', 'cash')]).write({'ps_voucher_word': '1', 'ps_voucher_name':'现金凭证'})
    #     self.search([('ps_voucher_word', '=', None), ( 'type', '=', 'bank')]).write({'ps_voucher_word': '2', 'ps_voucher_name':'银行凭证'})
    #     return res

    @api.model
    def create(self, vals):
        # 由用户界面添加银行或者现金类的账簿在保存前要录入借贷方科目
        if self._context.get('check_account_validate'):
            if vals.get('type') in ('bank', 'cash'):
                if (vals.get('default_debit_account_id',False)==False) or (vals.get('default_credit_account_id',False)==False):
                    raise UserError(_("Under Bank or cash account, please maintain the default debit and credit account!"))

        journal = super().create(vals)
        return journal

    @api.multi
    def write(self, vals):
        # 由用户界面添加银行或者现金类的账簿在保存前要录入借贷方科目
        if self._context.get('check_account_validate'):
            if vals.get('type') in ('bank', 'cash'):
                if (vals.get('default_debit_account_id', False) == False) or (
                        vals.get('default_credit_account_id', False) == False):
                    raise UserError(_("Under Bank or cash account, please maintain the default debit and credit account!"))
        journal = super().write(vals)
        return journal